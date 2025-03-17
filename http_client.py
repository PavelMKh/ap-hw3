import httpx
import json

from config import TINY_URL_TOKEN

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