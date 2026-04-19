import json
from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

SETTING_FILES = (".env", "src/config/settings.env")


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=SETTING_FILES,
        env_prefix="APP_",
        extra="ignore",
    )

    NAME: str = "SmartFX API"
    VERSION: str = "0.1.0"
    ENV: str = "development"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    RELOAD: bool = False
    ENDPOINT_PREFIX: str = "/api"
    ALLOWED_ORIGINS: str = "*"
    SECRET_KEY: str = "smartfx-local-dev-secret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    @computed_field
    @property
    def allowed_origins(self) -> list[str]:
        value = self.ALLOWED_ORIGINS
        if not value:
            return ["*"]
        if value.startswith("["):
            return [item.strip() for item in json.loads(value) if item.strip()]
        return [item.strip() for item in value.split(",") if item.strip()]


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=SETTING_FILES,
        env_prefix="DB_",
        extra="ignore",
    )

    URL: str = "sqlite+aiosqlite:///./smartfx.db"
    ECHO: bool = False


class RateSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=SETTING_FILES,
        env_prefix="RATE_",
        extra="ignore",
    )

    PROVIDER: str = "mock"
    EXCHANGE_RATE_API_URL: str = "https://v6.exchangerate-api.com/v6"
    EXCHANGE_RATE_API_KEY: str = ""
    CACHE_TTL_SECONDS: int = 300


class AISettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=SETTING_FILES,
        env_prefix="AI_",
        extra="ignore",
    )

    PROVIDER: str = "mock"
    MODEL: str = "moonshot-v1-8k"
    API_KEY: str = ""
    BASE_URL: str = "https://api.moonshot.cn/v1"


class Config:
    APP = AppSettings()
    DB = DatabaseSettings()
    RATE = RateSettings()
    AI = AISettings()


@lru_cache(maxsize=1)
def get_settings() -> Config:
    return Config()


SETTINGS = get_settings()
