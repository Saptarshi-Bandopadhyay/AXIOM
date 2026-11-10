"""Unit tests for application configuration and settings loading."""

from pathlib import Path
from app.config import get_settings


def test_default_settings_load_successfully() -> None:
    """Verify that Settings loads with valid default configuration values."""
    settings = get_settings()

    assert settings.PROJECT_NAME == "ReproCheck API"
    assert settings.APP_ENV in ("development", "testing")
    assert "postgresql+asyncpg://" in settings.DATABASE_URL
    assert settings.PRIMARY_MODEL == "gemini/gemini-3.1-flash-lite"
    assert settings.MAX_UPLOAD_SIZE_BYTES == 20 * 1024 * 1024
    assert isinstance(settings.UPLOAD_DIR, Path)


def test_get_settings_returns_cached_instance() -> None:
    """Verify that get_settings() returns the cached singleton instance."""
    instance_one = get_settings()
    instance_two = get_settings()
    assert instance_one is instance_two
