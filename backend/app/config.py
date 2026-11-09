"""Application settings for ReproCheck."""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "ReproCheck API"
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/reprocheck"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/reprocheck"
    DB_ECHO: bool = False

    REDIS_URL: str = "redis://localhost:6379/0"

    UPLOAD_DIR: Path = Path("storage/uploads")
    MAX_UPLOAD_SIZE_BYTES: int = 20 * 1024 * 1024

    PRIMARY_MODEL: str = "gemini/gemini-1.5-flash"
    FALLBACK_MODEL: str = "groq/llama-3.3-70b-versatile"
    FAST_CHEAP_MODEL: str = "groq/llama-3.1-8b-instant"

    GEMINI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None

    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: str | None = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
