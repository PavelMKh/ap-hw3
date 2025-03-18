import httpx
import json
import logging

from config import TINY_URL_TOKEN

logging.basicConfig(level=logging.INFO)

async def create_short_url(url: str, api_token: str = TINY_URL_TOKEN) -> tuple or None:
    """
    Сокращает URL-адрес с помощью API TinyURL.
    """

    api_url = "https://api.tinyurl.com/create"
    payload = {
        "url": url,
        "domain": "tinyurl.com",
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(api_url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            if "data" in data and "tiny_url" in data["data"]:
                return response.status_code, data["data"]["tiny_url"]
            else:
                print(f"Неожиданный ответ: {data}")
                return None
        except httpx.HTTPStatusError as e:
            print(f"HTTP error: {e}")
            return None
        except httpx.RequestError as e:
            print(f"Ошибка запроса: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Ошибка декодирования JSON: {e}")
            return None
        
async def delete_short_url(alias: str, api_token: str = TINY_URL_TOKEN) -> tuple or None:
    """
    Удаляет алиас с TinyURL.
    """

    api_url = f"https://api.tinyurl.com/alias/tinyurl.com/{alias}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(api_url, headers=headers)
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            print(f"HTTP error: {e}")
            return None
        except httpx.RequestError as e:
            print(f"Ошибка запроса: {e}")
            return None
        

async def update_short_url(alias: str, long_url: str, api_token: str = TINY_URL_TOKEN) -> tuple or None:
    """
    Удаляет алиас с TinyURL.
    """

    api_url = f"https://api.tinyurl.com/change"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}"
    }

    payload = {
        "url": long_url,
        "domain": "tinyurl.com",
        "alias": alias
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.patch(api_url, json=payload, headers=headers)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error: {e}")
            return None
        except httpx.RequestError as e:
            print(f"Ошибка запроса: {e}")
            return None