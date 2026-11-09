"""Application configuration management for ReproCheck.

Loads settings from environment variables and .env files using Pydantic Settings.
Centralizes database URLs, Redis connection, file storage paths, model routing,
and observability credentials.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """ReproCheck application settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        # Load from .env file located at backend/.env or parent root
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --------------------------------------------------------------------------
    # Application Environment
    # --------------------------------------------------------------------------
    PROJECT_NAME: str = Field(
        default="ReproCheck API",
        description="User-facing title of the application API.",
    )
    APP_ENV: Literal["development", "testing", "production"] = Field(
        default="development",
        description="Execution environment mode.",
    )
    DEBUG: bool = Field(
        default=False,
        description="Enable debug logging and detailed error responses.",
    )
    API_PREFIX: str = Field(
        default="/api/v1",
        description="Global URL route prefix for API endpoints.",
    )

    # --------------------------------------------------------------------------
    # Database Connections (PostgreSQL port 5432)
    # --------------------------------------------------------------------------
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/reprocheck",
        description="Asynchronous database URL for SQLAlchemy asyncpg engine.",
    )
    DATABASE_URL_SYNC: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/reprocheck",
        description="Synchronous database URL for Alembic migration commands.",
    )
    DB_ECHO: bool = Field(
        default=False,
        description="Log generated SQL queries to stdout for debugging.",
    )

    # --------------------------------------------------------------------------
    # Cache Connection (Redis port 6379)
    # --------------------------------------------------------------------------
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Connection string for local Redis cache.",
    )

    # --------------------------------------------------------------------------
    # File Storage
    # --------------------------------------------------------------------------
    UPLOAD_DIR: Path = Field(
        default=Path("storage/uploads"),
        description="Local directory for storing uploaded research paper PDFs.",
    )
    MAX_UPLOAD_SIZE_BYTES: int = Field(
        default=20 * 1024 * 1024,
        description="Maximum allowed PDF upload size in bytes (20 MB default).",
    )

    # --------------------------------------------------------------------------
    # Model Gateway Configuration (Free Gemini and Groq models)
    # --------------------------------------------------------------------------
    PRIMARY_MODEL: str = Field(
        default="gemini/gemini-1.5-flash",
        description="Primary language model for classification and review tasks.",
    )
    FALLBACK_MODEL: str = Field(
        default="groq/llama-3.3-70b-versatile",
        description="Fallback model invoked if primary model hits rate limit or error.",
    )
    FAST_CHEAP_MODEL: str = Field(
        default="groq/llama-3.1-8b-instant",
        description="Fast model for light heuristics and validation tasks.",
    )

    # API Keys for Model Providers
    GEMINI_API_KEY: str | None = Field(
        default=None,
        description="Google Gemini API key for gemini-* models.",
    )
    GROQ_API_KEY: str | None = Field(
        default=None,
        description="Groq API key for llama-* models.",
    )

    # --------------------------------------------------------------------------
    # Observability Configuration (Langfuse)
    # --------------------------------------------------------------------------
    LANGFUSE_PUBLIC_KEY: str | None = Field(
        default=None,
        description="Langfuse project public key.",
    )
    LANGFUSE_SECRET_KEY: str | None = Field(
        default=None,
        description="Langfuse project secret key.",
    )
    LANGFUSE_HOST: str = Field(
        default="https://cloud.langfuse.com",
        description="Langfuse API host URL.",
    )

    @field_validator("UPLOAD_DIR", mode="after")
    @classmethod
    def ensure_upload_dir_path(cls, v: Path | str) -> Path:
        """Convert string path to Path object."""
        return Path(v) if isinstance(v, str) else v

    @property
    def is_langfuse_configured(self) -> bool:
        """Determine whether Langfuse credentials are provided."""
        return bool(self.LANGFUSE_PUBLIC_KEY and self.LANGFUSE_SECRET_KEY)

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.APP_ENV == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton instance of application settings.

    Uses lru_cache to parse environment variables only once per process life.
    Can be cleared in tests via `get_settings.cache_clear()`.

    Returns:
        Settings: Configured settings instance.
    """
    return Settings()
