import pytest_asyncio
import pytest
from repository import Repository 

@pytest_asyncio.fixture
async def db():
    db_url = "postgresql://myuser:mypassword@localhost:5435/mydb"
    repo = Repository(db_url)
    await repo.connect()
    await repo.create_table()
    yield repo
    await repo.close()

@pytest.mark.asyncio
async def test_create_and_find_user(db):
    user = await db.find_user_by_token_and_id(1, 'token1')
    assert user is not None
    assert user['id'] == 1
    assert user['token'] == 'token1'

    user = await db.find_user_by_token_and_id(2, 'wrong_token')
    assert user is None

@pytest.mark.asyncio
async def test_save_and_find_link(db):
    await db.save_link_with_user("http://test_link.com", "short_link", 1, True, None)
    link = await db.find_original_url_by_short_code("short_link")
    assert link == "http://test_link.com"

@pytest.mark.asyncio
async def test_delete_link(db):
    await db.save_link_with_user("http://test_link.com", "short_link", 1, True, None)
    await db.delete_link("short_link")
    link = await db.find_original_url_by_short_code("short_link")
    assert link is None

@pytest.mark.asyncio
async def test_update_long_link(db):
    await db.save_link_with_user("http://test_link.com", "short_link", 1, True, None)
    await db.update_long_link("short_link", "http://test_link2.com")
    link = await db.find_original_url_by_short_code("short_link")
    assert link == "http://test_link2.com"

@pytest.mark.asyncio
async def test_get_link_stats(db):
    await db.save_link_with_user("http://test_link.com", "short_link", 1, True, None)
    await db.save_access_statistics("short_link")
    stats = await db.get_link_stats("short_link")
    assert stats['short_url'] == "short_link"
    assert stats['full_url'] == "http://test_link.com"
    assert stats['transitions_count'] == 1

@pytest.mark.asyncio
async def test_check_alias_availability(db):
    await db.save_link_with_user("http://test_link.com", "short_link", 1, True, None)
    available = await db.check_alias_availability("short_link")
    assert not available
    available = await db.check_alias_availability("short_link_2")
    assert available

@pytest.mark.asyncio
async def test_get_links_overview(db):
    await db.save_link_with_user("http://test_link.com", "short_link", 1, True, None)
    overview = await db.get_links_overview(1)
    assert overview['active_links'] == 1
    assert overview['expired_links'] == 0

if __name__ == "__main__":
    pytest.main()