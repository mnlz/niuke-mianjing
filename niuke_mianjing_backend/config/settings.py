from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_CHARSET: str

    FEISHU_WEBHOOK: Optional[str] = None

    WECHAT_APP_ID: Optional[str] = None
    WECHAT_APP_SECRET: Optional[str] = None
    WECHAT_AUTHOR: str

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str
    OPENAI_CHAT_COMPLETIONS_URL: str
    OPENAI_IMAGE_GENERATIONS_URL: Optional[str] = None
    OPENAI_TEXT_MODEL: str
    OPENAI_IMAGE_MODEL: str

    PROXY_HOST: str
    PROXY_PORT: int

    MAX_PAGES: int
    SLEEP_INTERVAL: int

    API_HOST: str
    API_PORT: int

    API_KEY: Optional[str] = None

    class Config:
        env_file = PROJECT_ROOT / ".env"
        env_file_encoding = "utf-8"


settings = Settings()


def get_db_config():
    return {
        "host": settings.DB_HOST,
        "port": settings.DB_PORT,
        "user": settings.DB_USER,
        "password": settings.DB_PASSWORD,
        "database": settings.DB_NAME,
        "charset": settings.DB_CHARSET,
    }


def get_proxy_config():
    return {
        "http": f"http://{settings.PROXY_HOST}:{settings.PROXY_PORT}",
        "https": f"http://{settings.PROXY_HOST}:{settings.PROXY_PORT}",
    }
