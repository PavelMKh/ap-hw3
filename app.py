import os
import logging

from fastapi import FastAPI, HTTPException, Request
from service import Service
from repository import Repository
from entity import LinkRequest
from fastapi.responses import RedirectResponse

logging.basicConfig(level=logging.INFO)

my_app = FastAPI()

db_url = os.environ.get('DATABASE_URL')
repo = Repository(db_url)

service = Service(repo)

@my_app.on_event("startup")
async def startup_event():
    await repo.connect()
    await repo.create_table()

@my_app.on_event("shutdown")
async def shutdown_event():
    await repo.close()

@my_app.post('/links/shorten')
async def get_short_link(request: Request, link_request: LinkRequest):
    user_id = request.headers.get('X-User-Id')
    token = request.headers.get('Authorization').split()[1] if request.headers.get('Authorization') else None
    
    logging.info(f"Запрос от пользователя: {user} на создание короткой ссылки")

    if user_id and token:
        user = await repo.find_user_by_token_and_id(int(user_id), token)
        if user:
            result = await service.create_short_link(link_request.link, int(user_id), True)
            if result:
                return {
                    "status_code": result['status_code'],
                    "short_link": result['short_link']
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to shorten link")
        else:
            raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        result = await service.create_short_link(link_request.link, None, False)
        if result:
            return {
                "status_code": result['status_code'],
                "short_link": result['short_link']
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to shorten link")
        
@my_app.get('/links/{short_code}')
async def redirect_to_original_url(short_code: str):
    short_url = f"https://tinyurl.com/{short_code}"
    logging.info(f"Запрос на переход по короткой ссылке: {short_url}")
    original_url = await service.get_original_url(short_url)
    if original_url:
        return RedirectResponse(url=original_url, status_code=302)
    else:
        raise HTTPException(status_code=404, detail="Link not found")
    

@my_app.delete('/links/{short_code}')
async def delete_link(short_code: str, request: Request):
    user_id = request.headers.get('X-User-Id')
    token = request.headers.get('Authorization').split()[1] if request.headers.get('Authorization') else None

    logging.info(f"Запрос от пользователя: {user_id} на удаление короткой ссылки по коду: {short_code}")

    if user_id and token:
        if await service.delete_link(short_code, int(user_id), token):
            return {"message": "Link has been deleted"}
        else:
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
@my_app.put('/links/{short_code}')
async def update_link(short_code: str, request: Request, link_request: LinkRequest):
    user_id = request.headers.get('X-User-Id')
    token = request.headers.get('Authorization').split()[1] if request.headers.get('Authorization') else None

    logging.info(f"Запрос от пользователя: {user_id} на изменение короткой ссылки по коду: {short_code}")
    
    if user_id and token:
        if await service.update_url(short_code, link_request.link, int(user_id), token):
            return {"message": "Link has been updated"}
        else:
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")