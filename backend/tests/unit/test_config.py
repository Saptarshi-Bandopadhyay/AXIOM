"""Tests for application configuration."""

from pathlib import Path
from app.config import get_settings


def test_settings_load() -> None:
    settings = get_settings()
    assert settings.PROJECT_NAME == "ReproCheck API"
    assert "postgresql+asyncpg://" in settings.DATABASE_URL
    assert isinstance(settings.UPLOAD_DIR, Path)
