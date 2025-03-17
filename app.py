import os

from fastapi import FastAPI, HTTPException, Request
from service import Service
from repository import Repository
from entity import LinkRequest

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