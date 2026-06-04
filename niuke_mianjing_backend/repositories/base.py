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
