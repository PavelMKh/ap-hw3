import asyncio
from http_client import create_short_url
from repository import Repository
from typing import Optional

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