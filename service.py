import asyncio
import logging

from http_client import create_short_url, delete_short_url, update_short_url
from repository import Repository
from typing import Optional

logging.basicConfig(level=logging.INFO)

class Service:
    _instance = None

    def __new__(cls, repository: Repository):
        if cls._instance is None:
            cls._instance = super(Service, cls).__new__(cls)
            cls._instance.repository = repository
        return cls._instance

    async def create_short_link(self, full_link: str, user_id: int = None, is_authorized: bool = False) -> Optional[dict]:
        result = await create_short_url(full_link)
        if result:
            status_code, short_link = result
            await self.repository.save_link_with_user(full_link, short_link, user_id, is_authorized)
            return {
                "status_code": status_code,
                "short_link": short_link
            }
        else:
            return None
        
    async def get_original_url(self, short_code: str):
        return await self.repository.find_original_url_by_short_code(short_code)
    
    async def delete_link(self, short_code: str, user_id: int, token: str) -> bool:
        user = await self.repository.find_user_by_token_and_id(user_id, token)
        if user:
            short_url = f"https://tinyurl.com/{short_code}"
            author_id = await self.repository.get_link_author(short_url)
            alias = short_code.split("/")[-1]
            if user['id'] == author_id:
                await self.repository.delete_link(short_code)
                await delete_short_url(alias)
                return True
            else:
                return False
        else:
            return False
        
    async def update_url(self, short_code: str, long_url: str, user_id: int, token: str) -> bool:
        user = await self.repository.find_user_by_token_and_id(user_id, token)
        if user:
            short_url = f"https://tinyurl.com/{short_code}"
            author_id = await self.repository.get_link_author(short_url)
            alias = short_url.split("/")[-1]
            if user['id'] == author_id:
                logging.info('направление запроса в БД')
                await self.repository.update_long_link(short_url, long_url)
                await update_short_url(alias, long_url)
                return True
            else:
                return False
        else:
            return False
        
        