import re

from niuke_mianjing_backend.repositories.database import DatabasePool


class BaseRepository:
    async def _fetch_one(self, query: str, params: tuple = None):
        pool = await DatabasePool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                return await cur.fetchone()

    async def _fetch_all(self, query: str, params: tuple = None):
        pool = await DatabasePool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                return await cur.fetchall()

    async def _execute(self, query: str, params: tuple = None):
        create_match = re.search(r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+`?([a-zA-Z0-9_]+)`?", query, re.I)
        if create_match:
            exists = await self._fetch_one(
                """
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = DATABASE() AND table_name = %s
                """,
                (create_match.group(1),),
            )
            if exists and exists[0] > 0:
                return 0
        pool = await DatabasePool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                return cur.rowcount

    async def _execute_lastrowid(self, query: str, params: tuple = None):
        pool = await DatabasePool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                return cur.lastrowid

    async def _execute_many(self, query: str, params_list: list):
        pool = await DatabasePool.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.executemany(query, params_list)
                return cur.rowcount
