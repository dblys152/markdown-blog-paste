from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "MD2Blog API"
    environment: str = "local"
    database_url: str = "postgresql+asyncpg://md2blog:md2blog@localhost:5432/md2blog"
    migration_database_url: str = "postgresql+psycopg://md2blog:md2blog@localhost:5432/md2blog"


@lru_cache
def get_settings() -> Settings:
    return Settings()
