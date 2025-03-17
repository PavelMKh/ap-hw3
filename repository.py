import asyncpg

class Repository:
    _instance = None

    def __new__(cls, db_url: str):
        if cls._instance is None:
            cls._instance = super(Repository, cls).__new__(cls)
            cls._instance.db_url = db_url
            cls._instance.pool = None
        return cls._instance

    async def connect(self):
        self.pool = await asyncpg.create_pool(self.db_url)

    async def create_table(self):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                DROP TABLE IF EXISTS links;
            """)
            await conn.execute("""
                DROP TABLE IF EXISTS users;
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    token TEXT NOT NULL
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    id SERIAL PRIMARY KEY,
                    full_link VARCHAR(255) NOT NULL,
                    short_link VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER,
                    is_authorized BOOLEAN DEFAULT FALSE
                );
            """)
            await conn.execute("""
                INSERT INTO users (id, token)
                VALUES (1, 'token1'), (2, 'token2');
            """)

    async def find_user_by_token_and_id(self, user_id: int, token: str):
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT * FROM users WHERE id = $1 AND token = $2
            """, user_id, token)
            if result:
                return dict(result)
            else:
                return None

    async def save_link_with_user(self, full_link: str, short_link: str, user_id: int, is_authorized: bool):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO links (full_link, short_link, user_id, is_authorized)
                VALUES ($1, $2, $3, $4)
            """, full_link, short_link, user_id, is_authorized)

    async def close(self):
        if self.pool:
            await self.pool.close()