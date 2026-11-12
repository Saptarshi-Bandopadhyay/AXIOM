"""Application configuration management for ReproCheck.

Loads settings from environment variables and .env files using Pydantic Settings.
"""

from functools import lru_cache
from pathlib import Path
from pydantic import field_validator, model_validator
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

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_async_database_url(cls, v: str | None) -> str:
        """Sanitize DATABASE_URL to use asyncpg driver."""
        if not v:
            return "postgresql+asyncpg://postgres:postgres@localhost:5432/reprocheck"

        url = str(v).strip()
        # Correct typo 'postgresql+async://' -> 'postgresql+asyncpg://'
        if url.startswith("postgresql+async://"):
            url = "postgresql+asyncpg://" + url[len("postgresql+async://") :]
        # Convert legacy 'postgres://' or sync 'postgresql://' to asyncpg
        elif url.startswith("postgres://"):
            url = "postgresql+asyncpg://" + url[len("postgres://") :]
        elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
            url = "postgresql+asyncpg://" + url[len("postgresql://") :]

        return url

    @field_validator("DATABASE_URL_SYNC", mode="before")
    @classmethod
    def normalize_sync_database_url(cls, v: str | None) -> str:
        """Sanitize DATABASE_URL_SYNC to use standard sync driver."""
        if not v:
            return "postgresql://postgres:postgres@localhost:5432/reprocheck"

        url = str(v).strip()
        if url.startswith("postgresql+asyncpg://"):
            url = "postgresql://" + url[len("postgresql+asyncpg://") :]
        elif url.startswith("postgresql+async://"):
            url = "postgresql://" + url[len("postgresql+async://") :]
        elif url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://") :]

        return url

    @model_validator(mode="after")
    def sync_database_urls(self) -> "Settings":
        """Auto-derive DATABASE_URL_SYNC if only DATABASE_URL was configured."""
        if self.DATABASE_URL and (
            not self.DATABASE_URL_SYNC
            or "localhost:5432" in self.DATABASE_URL_SYNC
            and "localhost:5432" not in self.DATABASE_URL
        ):
            url = self.DATABASE_URL
            if url.startswith("postgresql+asyncpg://"):
                self.DATABASE_URL_SYNC = "postgresql://" + url[len("postgresql+asyncpg://") :]
            elif url.startswith("postgresql://"):
                self.DATABASE_URL_SYNC = url
        return self

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
