"""Application configuration management for ReproCheck.

Loads settings from environment variables and .env files using Pydantic Settings.
"""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --------------------------------------------------------------------------
    # Application Environment
    # --------------------------------------------------------------------------
    PROJECT_NAME: str = "ReproCheck API"
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"

    # --------------------------------------------------------------------------
    # Database Connections (PostgreSQL port 5432)
    # --------------------------------------------------------------------------
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/reprocheck"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/reprocheck"
    DB_ECHO: bool = False

    # --------------------------------------------------------------------------
    # Cache Connection (Redis port 6379)
    # --------------------------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"

    # --------------------------------------------------------------------------
    # File Storage
    # --------------------------------------------------------------------------
    UPLOAD_DIR: Path = Path("storage/uploads")
    MAX_UPLOAD_SIZE_BYTES: int = 20 * 1024 * 1024  # 20 MB

    # --------------------------------------------------------------------------
    # Model Gateway Configuration (Free Gemini and Groq models)
    # --------------------------------------------------------------------------
    PRIMARY_MODEL: str = "gemini/gemini-3.1-flash-lite"
    FALLBACK_MODEL: str = "groq/openai/gpt-oss-120b"
    FAST_CHEAP_MODEL: str = "groq/openai/gpt-oss-20b"

    GEMINI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None

    # --------------------------------------------------------------------------
    # Observability Configuration (Langfuse)
    # --------------------------------------------------------------------------
    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: str | None = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton instance of application settings."""
    return Settings()
