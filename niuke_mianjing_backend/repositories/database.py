import aiomysql
from niuke_mianjing_backend.config import get_db_config


class DatabasePool:
    _pool: aiomysql.Pool = None

    @classmethod
    async def init(cls, db_config: dict = None):
        config = db_config or get_db_config()
        cls._pool = await aiomysql.create_pool(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            db=config["database"],
            charset=config["charset"],
            minsize=2,
            maxsize=10,
            autocommit=True,
        )
        return cls._pool

    @classmethod
    async def get_pool(cls) -> aiomysql.Pool:
        if cls._pool is None:
            await cls.init()
        return cls._pool

    @classmethod
    async def close(cls):
        if cls._pool:
            cls._pool.close()
            await cls._pool.wait_closed()
            cls._pool = None

    @classmethod
    async def acquire(cls):
        pool = await cls.get_pool()
        conn = await pool.acquire()
        try:
            yield conn
        finally:
            pool.release(conn)
