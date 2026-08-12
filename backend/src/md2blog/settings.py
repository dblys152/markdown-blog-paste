from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL, make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.local", env_file_encoding="utf-8")

    app_name: str = "MD2Blog API"
    environment: str = "local"
    database_url: str = "postgresql://md2blog:md2blog@localhost:5432/md2blog"
    migration_database_url: str = "postgresql://md2blog:md2blog@localhost:5432/md2blog"
    jwt_secret_key: SecretStr = SecretStr("local-development-secret-change-me")
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 14
    refresh_token_cookie_secure: bool = False
    refresh_token_cookie_samesite: str = "lax"

    @property
    def async_database_url(self) -> URL:
        url = make_url(self.database_url)
        query = dict(url.query)
        ssl_mode = query.pop("sslmode", None)
        query.pop("channel_binding", None)
        if ssl_mode is not None:
            query["ssl"] = ssl_mode
        return url.set(drivername="postgresql+asyncpg", query=query)

    @property
    def sync_migration_database_url(self) -> URL:
        return make_url(self.migration_database_url).set(drivername="postgresql+psycopg")


@lru_cache
def get_settings() -> Settings:
    return Settings()
