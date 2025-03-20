import asyncio
import logging
import random
import string

from repository import Repository
from typing import Optional
from fastapi import HTTPException
from datetime import datetime

logging.basicConfig(level=logging.INFO)

class Service:
    _instance = None

    def __new__(cls, repository: Repository):
        if cls._instance is None:
            cls._instance = super(Service, cls).__new__(cls)
            cls._instance.repository = repository
        return cls._instance

        
    async def get_original_url(self, short_code: str):
        await self.repository.save_access_statistics(short_code)
        return await self.repository.find_original_url_by_short_code(short_code)
    

    async def delete_link(self, short_code: str, user_id: int, token: str) -> bool:
        user = await self.repository.find_user_by_token_and_id(user_id, token)
        if user:
            author_id = await self.repository.get_link_author(short_code)
            if user['id'] == author_id:
                await self.repository.delete_link(short_code)
                return True
            else:
                return False
        else:
            return False
        

    async def update_url(self, short_code: str, long_url: str, user_id: int, token: str) -> bool:
        user = await self.repository.find_user_by_token_and_id(user_id, token)
        if user:
            author_id = await self.repository.get_link_author(short_code)
            if user['id'] == author_id:
                await self.repository.update_long_link(short_code, long_url)
                return True
            else:
                return False
        else:
            return False
        

    async def get_stats(self, short_code: str, user_id: int, token: str):
        user = await self.repository.find_user_by_token_and_id(user_id, token)
        if not user:
            return None

        author_id = await self.repository.get_link_author(short_code)

        if author_id is None:
            return None

        if user['id'] != author_id:
            return None

        stats = await self.repository.get_link_stats(short_code)
        if stats:
            return stats
        else:
            return None
        

    async def create_short_link(self, full_link: str, user_id: int = None, is_authorized: bool = False, expires_at: Optional[datetime] = None) -> Optional[dict]:
        symbols = string.ascii_letters + string.digits
        max_attempts = 50
        attempts = 0
        
        while attempts < max_attempts:
            short_link = ''.join(random.choice(symbols) for _ in range(6))
            
            if await self.repository.find_original_url_by_short_code(short_link) is None:
                break
            attempts += 1
        
        if attempts == max_attempts:
            return None
        
        await self.repository.save_link_with_user(full_link, short_link, user_id, is_authorized, expires_at)
        
        return {
            "status_code": 201,
            "short_link": short_link
        }
    
    
    async def create_short_link_with_custom_alias(self, full_link: str, custom_alias: str, user_id: int = None, is_authorized: bool = False, expires_at: Optional[datetime] = None) -> Optional[dict]:
        if await self.repository.find_original_url_by_short_code(custom_alias):
            raise HTTPException(status_code=400, detail="Alias already exists")
        
        await self.repository.save_link_with_user(full_link, custom_alias, user_id, is_authorized, expires_at)
        
        return {
            "status_code": 201,
            "short_link": custom_alias
        }
    

    async def get_links_overview(self, user_id: int):
        return await self.repository.get_links_overview(user_id)
    
    
    async def find_short_link_by_original_url(self, original_url: str) -> Optional[dict]:
        logging.info("Попали в сервисный класс")
        return await self.repository.find_short_link_by_original_url(original_url)
    