import asyncpg
import logging

from fastapi.encoders import jsonable_encoder

logging.basicConfig(level=logging.INFO)

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
                    expires_at TIMESTAMP,
                    user_id INTEGER,
                    is_authorized BOOLEAN DEFAULT FALSE
                );
            """)


            await conn.execute("""
                CREATE TABLE IF NOT EXISTS statistics (
                    id SERIAL PRIMARY KEY,
                    short_link VARCHAR(255) NOT NULL,
                    access_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)


            await conn.execute("""
                CREATE TABLE IF NOT EXISTS expired_links (
                    id SERIAL PRIMARY KEY,
                    full_link VARCHAR(255) NOT NULL,
                    short_link VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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


    async def save_link_with_user(self, full_link: str, short_link: str, user_id: int, is_authorized: bool, expires_at):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO links (full_link, short_link, user_id, is_authorized, expires_at)
                VALUES ($1, $2, $3, $4, $5)
            """, full_link, short_link, user_id, is_authorized, expires_at)


    async def find_original_url_by_short_code(self, short_url: str):
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT full_link FROM links WHERE short_link = $1
            """, short_url)
            if result:
                return result['full_link']
            else:
                return None
            
    async def get_link_author(self, short_url: str):
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT user_id FROM links WHERE short_link = $1
            """, short_url)
            if result:
                return result['user_id']
            else:
                return None
    
    async def delete_link(self, short_url: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM links WHERE short_link = $1
            """, short_url)

    
    async def update_long_link(self, short_link: str, long_link: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE links SET full_link = $1 WHERE short_link = $2
            """, long_link, short_link)

    
    async def get_creation_date_by_short_link(self, short_link: str):
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT created_at FROM links WHERE short_link = $1
            """, short_link)
            
            if result:
                return result['created_at']
            else:
                return None
            

    async def save_access_statistics(self, short_url: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO statistics (short_link)
                VALUES ($1)
            """, short_url)


    async def get_link_stats(self, short_url: str):
        async with self.pool.acquire() as conn:
            link_info_result = await conn.fetchrow("""
                SELECT full_link, created_at FROM links WHERE short_link = $1
            """, short_url)
            
            if link_info_result:
                full_link = link_info_result['full_link']
                creation_date = link_info_result['created_at']
            else:
                return None
            
            transitions_count_result = await conn.fetchrow("""
                SELECT COUNT(*) FROM statistics WHERE short_link = $1
            """, short_url)
            
            if transitions_count_result:
                transitions_count = transitions_count_result['count']
            else:
                transitions_count = 0
            
            last_use_date_result = await conn.fetchrow("""
                SELECT MAX(access_date) FROM statistics WHERE short_link = $1
            """, short_url)
            
            if last_use_date_result and last_use_date_result['max'] is not None:
                last_use_date = last_use_date_result['max']
            else:
                last_use_date = None
            
            stats = {
                "short_url": short_url,
                "full_url": full_link,
                "creation_date": creation_date,
                "transitions_count": transitions_count,
                "last_use_date": last_use_date
            }
            
            return jsonable_encoder(stats)
        

    async def check_alias_availability(self, alias: str) -> bool:
        return await self.find_original_url_by_short_code(alias) is None


    async def find_short_link_by_original_url(self, original_url: str):
        async with self.pool.acquire() as conn:
            logging.info("Запрос на поиск ссылки")
            result = await conn.fetchrow("""
                SELECT short_link FROM links WHERE full_link = $1
            """, original_url)
            logging.info(f"Результат запроса: {result}")
            if result:
                return {"short_link": result['short_link']}
            else:
                return None
            
    
    async def delete_expired_links(self):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                    INSERT INTO expired_links (full_link, short_link, created_at, expires_at, user_id, is_authorized)
                    SELECT full_link, short_link, created_at, expires_at, user_id, is_authorized
                    FROM links
                    WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP
                """)
                
                await conn.execute("""
                    DELETE FROM links WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP
                """)


    async def get_links_overview(self, user_id: int):
        async with self.pool.acquire() as conn:
            async with conn.transaction():    
                active_links_count = await conn.fetchval("""
                        SELECT COUNT(*) 
                        FROM links 
                        WHERE user_id = $1 AND expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP;
                    """, int(user_id))
                    
                if active_links_count is None:
                        active_links_count = 0
                    
                expired_links_count = await conn.fetchval("""
                        SELECT COUNT(*) 
                        FROM expired_links 
                        WHERE user_id = $1;
                    """, int(user_id))
                    
                if expired_links_count is None:
                        expired_links_count = 0
                    
                return {
                        "active_links": active_links_count,
                        "expired_links": expired_links_count
                    }

    async def close(self):
        if self.pool:
            await self.pool.close()

            