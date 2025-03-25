import pytest
import httpx
import subprocess
from datetime import datetime, timedelta
from entity import LinkRequest, CustomLinkRequest

@pytest.fixture
def client():
    return httpx.AsyncClient(base_url="http://localhost:8000")

@pytest.mark.asyncio
async def test_shorten_link_anonymous(client):
    response = await client.post(
        "/links/shorten",
        json={"link": "https://example.com", "expires_at": None}
    )
    assert response.status_code == 201
    assert "short_link" in response.json()

@pytest.mark.asyncio
async def test_shorten_link_custom_alias(client):
    headers = {
        "X-User-Id": "1",
        "Authorization": "Bearer token1"
    }
    response = await client.post(
        "/links/custom_shorten",
        json={
            "link": "https://example.com",
            "custom_alias": "custom",
            "expires_at": None
        },
        headers=headers
    )
    assert response.status_code == 201
    assert response.json()["short_link"] == "custom"

@pytest.mark.asyncio
async def test_shorten_link_duplicate_alias(client):
    await client.post(
        "/links/custom_shorten",
        json={
            "link": "https://example.com",
            "custom_alias": "duplicate",
            "expires_at": None
        }
    )
    response = await client.post(
        "/links/custom_shorten",
        json={
            "link": "https://example.com",
            "custom_alias": "duplicate",
            "expires_at": None
        }
    )
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_redirect(client):
    short_link = 'custom'
    response = await client.get(f"/links/{short_link}")
    assert response.status_code == 302

@pytest.mark.asyncio
async def test_update_link(client):
    short_link = 'custom'
    
    headers = {
        "X-User-Id": "1",
        "Authorization": "Bearer token1"
    }
    response = await client.put(
        f"/links/{short_link}",
        json={"link": "https://new.example.com", "expires_at": None},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Link has been updated"

@pytest.mark.asyncio
async def test_delete_link(client):
    short_link = 'custom'
    
    headers = {
        "X-User-Id": "1",
        "Authorization": "Bearer token1"
    }
    response = await client.delete(
        f"/links/{short_link}",
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Link has been deleted"

@pytest.mark.asyncio
async def test_shorten_link_custom_alias2(client):
    headers = {
        "X-User-Id": "1",
        "Authorization": "Bearer token1"
    }
    response = await client.post(
        "/links/custom_shorten",
        json={
            "link": "https://example22.com",
            "custom_alias": "custom2",
            "expires_at": None
        },
        headers=headers
    )
    assert response.status_code == 201
    assert response.json()["short_link"] == "custom2"

@pytest.mark.asyncio
async def test_get_stats(client):
    short_link = 'custom2'
    
    headers = {
        "X-User-Id": "1",
        "Authorization": "Bearer token1"
    }
    response = await client.get(
        f"/links/{short_link}/stats",
        headers=headers
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_search_link(client):
    original_url = "https://example22.com"
    short_link = 'custom2'
    
    response = await client.get(f"/search?original_url={original_url}")
    assert response.status_code == 200
    assert response.json()["short_link"] == short_link

@pytest.mark.asyncio
async def test_get_links_overview(client):
    headers = {
        "X-User-Id": "1",
        "Authorization": "Bearer token1"
    }
    response = await client.get("/overview", headers=headers)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_expired_link(client):
    expires_at = datetime.now() - timedelta(days=1)
    short_link = 'custom2'
    
    response = await client.get(f"/links/{short_link}")
    assert response.status_code == 302
