"""Unit tests for application configuration and settings loading."""

import os
from pathlib import Path
import pytest
from app.config import Settings, get_settings


def test_default_settings_values() -> None:
    """Verify that default settings match project architectural choices."""
    settings = Settings()

    assert settings.PROJECT_NAME == "ReproCheck API"
    assert settings.API_PREFIX == "/api/v1"
    assert settings.APP_ENV in ("development", "testing")
    assert "postgresql+asyncpg://" in settings.DATABASE_URL
    assert "postgresql://" in settings.DATABASE_URL_SYNC
    assert settings.PRIMARY_MODEL == "gemini/gemini-1.5-flash"
    assert settings.FALLBACK_MODEL == "groq/llama-3.3-70b-versatile"
    assert settings.FAST_CHEAP_MODEL == "groq/llama-3.1-8b-instant"
    assert settings.MAX_UPLOAD_SIZE_BYTES == 20 * 1024 * 1024
    assert isinstance(settings.UPLOAD_DIR, Path)


def test_get_settings_caching() -> None:
    """Verify that get_settings() returns the same cached instance."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_langfuse_configured_property() -> None:
    """Verify is_langfuse_configured returns True only when both keys are provided."""
    unconfigured = Settings(LANGFUSE_PUBLIC_KEY=None, LANGFUSE_SECRET_KEY=None)
    assert unconfigured.is_langfuse_configured is False

    partial = Settings(LANGFUSE_PUBLIC_KEY="pk_test", LANGFUSE_SECRET_KEY=None)
    assert partial.is_langfuse_configured is False

    configured = Settings(
        LANGFUSE_PUBLIC_KEY="pk_test", LANGFUSE_SECRET_KEY="sk_test"
    )
    assert configured.is_langfuse_configured is True


def test_upload_dir_validator_converts_str_to_path() -> None:
    """Verify string paths passed to UPLOAD_DIR are automatically converted to Path."""
    s = Settings(UPLOAD_DIR="/tmp/custom_uploads")
    assert isinstance(s.UPLOAD_DIR, Path)
    assert s.UPLOAD_DIR == Path("/tmp/custom_uploads")


def test_environment_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that environment variables take precedence over default settings."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("PRIMARY_MODEL", "gemini/gemini-2.0-flash")

    s = Settings()
    assert s.APP_ENV == "production"
    assert s.is_production is True
    assert s.PRIMARY_MODEL == "gemini/gemini-2.0-flash"
