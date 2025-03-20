import os
import logging
import aioredis
import asyncio

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from service import Service
from repository import Repository
from entity import LinkRequest, CustomLinkRequest

logging.basicConfig(level=logging.INFO)

my_app = FastAPI()
scheduler = AsyncIOScheduler()

db_url = os.environ.get('DATABASE_URL')
repo = Repository(db_url)
service = Service(repo)

redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
redis = aioredis.from_url(redis_url, decode_responses=True)


@my_app.on_event("startup")
async def startup_event():
    await repo.connect()
    await repo.create_table()
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    
    scheduler.add_job(delete_expired_links, 'interval', minutes=1) 
    scheduler.start()


@my_app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    await repo.close()


@my_app.post('/links/shorten')
@cache(expire=60)
async def create_short_link(request: Request, link_request: LinkRequest):
    user_id = request.headers.get('X-User-Id')
    token = request.headers.get('Authorization').split()[1] if request.headers.get('Authorization') else None
    
    logging.info(f"Запрос от пользователя: {user_id} на создание короткой ссылки")

    if user_id and token:
        user = await repo.find_user_by_token_and_id(int(user_id), token)
        if user:
            result = await service.create_short_link(link_request.link, int(user_id), True, link_request.expires_at)
            if result:
                return JSONResponse(content={"short_link": result['short_link']}, status_code=201)
            else:
                raise HTTPException(status_code=500, detail="Failed to shorten link")
        else:
            raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        result = await service.create_short_link(link_request.link, None, False, link_request.expires_at)
        if result:
            return JSONResponse(content={"short_link": result['short_link']}, status_code=201)
        else:
            raise HTTPException(status_code=500, detail="Failed to shorten link")


@my_app.get('/links/{short_code}')
@cache(expire=60)
async def redirect_to_original_url(short_code: str):
    logging.info(f"Запрос на переход по короткой ссылке: {short_code}")
    original_url = await service.get_original_url(short_code)
    if original_url:
        return RedirectResponse(url=original_url, status_code=302)
    else:
        raise HTTPException(status_code=404, detail="Link not found")
    


@my_app.delete('/links/{short_code}')
@cache(expire=0)
async def delete_link(short_code: str, request: Request):
    user_id = request.headers.get('X-User-Id')
    token = request.headers.get('Authorization').split()[1] if request.headers.get('Authorization') else None

    logging.info(f"Запрос от пользователя: {user_id} на удаление короткой ссылки по коду: {short_code}")

    if user_id and token:
        if await service.delete_link(short_code, int(user_id), token):
            await redis.delete(f"fastapi-cache:{short_code}")
            return {"message": "Link has been deleted"}
        else:
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")


@my_app.put('/links/{short_code}')
@cache(expire=0)
async def update_link(short_code: str, request: Request, link_request: LinkRequest):
    user_id = request.headers.get('X-User-Id')
    token = request.headers.get('Authorization').split()[1] if request.headers.get('Authorization') else None

    logging.info(f"Запрос от пользователя: {user_id} на изменение короткой ссылки по коду: {short_code}")
    
    if user_id and token:
        if await service.update_url(short_code, link_request.link, int(user_id), token):
            await redis.delete(f"fastapi-cache:{short_code}")
            return {"message": "Link has been updated"}
        else:
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")


@my_app.get('/links/{short_code}/stats')
@cache(expire=60)
async def get_stats(short_code: str, request: Request):
    user_id = request.headers.get('X-User-Id')
    token = request.headers.get('Authorization').split()[1] if request.headers.get('Authorization') else None

    logging.info(f"Запрос от пользователя: {user_id} на предоставление статистики по коду: {short_code}")
    
    if not user_id or not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    stats = await service.get_stats(short_code, user_id_int, token)
    
    if stats is None:
        raise HTTPException(status_code=403, detail="Stats not found")
    
    return JSONResponse(content=stats, media_type="application/json")



@my_app.post('/links/custom_shorten')
@cache(expire=60)
async def create_custom_short_link(request: Request, link_request: CustomLinkRequest):
    user_id = request.headers.get('X-User-Id')
    token = request.headers.get('Authorization').split()[1] if request.headers.get('Authorization') else None
    
    logging.info(f"Запрос от пользователя: {user_id} на создание короткой ссылки с кастомным алиасом")

    if user_id and token:
        user = await repo.find_user_by_token_and_id(int(user_id), token)
        if user:
            result = await service.create_short_link_with_custom_alias(link_request.link, link_request.custom_alias, int(user_id), True, link_request.expires_at)
            if result:
                return JSONResponse(content={"short_link": result['short_link']}, status_code=201)
            else:
                raise HTTPException(status_code=500, detail="Failed to shorten link")
        else:
            raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        result = await service.create_short_link_with_custom_alias(link_request.link, link_request.custom_alias, None, False, link_request.expires_at)
        if result:
            return JSONResponse(content={"short_link": result['short_link']}, status_code=201)
        else:
            raise HTTPException(status_code=500, detail="Failed to shorten link")


@my_app.get('/search')
@cache(expire=60)
async def search_link_by_original_url(original_url: str):

    logging.info(f"Запрос на поиск ссылки {original_url}")

    if not original_url:
        raise HTTPException(status_code=400, detail="Original URL is required")
    
    result = await service.find_short_link_by_original_url(original_url)
    
    if result:
        return {
            "short_link": result['short_link']
        }
    else:
        raise HTTPException(status_code=404, detail="Link not found")


@my_app.get('/overview')
@cache(expire=60)
async def get_links_overview(request: Request):
    user_id = request.headers.get('X-User-Id')
    token = request.headers.get('Authorization').split()[1] if request.headers.get('Authorization') else None
    
    logging.info(f"Запрос от пользователя: {user_id} на получение статистики ссылок")

    if user_id and token:
        user = await repo.find_user_by_token_and_id(int(user_id), token)
        if user:
            return await service.get_links_overview(user_id)
        else:
            raise HTTPException(status_code=401, detail="Unauthorized")
 

async def delete_expired_links():
    await repo.delete_expired_links()