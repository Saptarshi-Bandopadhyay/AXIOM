"""Unit tests for configuration templates and connection string parsing."""

import os
from pathlib import Path
from urllib.parse import urlparse
import pytest


def test_env_example_exists_and_contains_expected_keys() -> None:
    """Verify that backend/.env.example exists and contains required service keys."""
    env_example = Path(__file__).resolve().parent.parent.parent / ".env.example"
    assert env_example.exists(), "backend/.env.example file must exist"

    content = env_example.read_text()
    required_keys = [
        "DATABASE_URL",
        "DATABASE_URL_SYNC",
        "REDIS_URL",
        "PRIMARY_MODEL",
        "FALLBACK_MODEL",
        "UPLOAD_DIR",
    ]
    for key in required_keys:
        assert f"{key}=" in content, f"Expected {key} in .env.example"


def test_docker_compose_file_exists_and_defines_services() -> None:
    """Verify that docker-compose.yml exists in project root with postgres and redis."""
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    compose_file = root_dir / "docker-compose.yml"
    assert compose_file.exists(), "docker-compose.yml must exist in workspace root"

    content = compose_file.read_text()
    assert "postgres:" in content
    assert "redis:" in content
    assert "5432:5432" in content
    assert "6379:6379" in content


def test_database_url_structure() -> None:
    """Verify default database URL parses cleanly with asyncpg dialect."""
    default_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/reprocheck"
    parsed = urlparse(default_url.replace("postgresql+asyncpg://", "postgresql://"))
    assert parsed.scheme == "postgresql"
    assert parsed.hostname == "localhost"
    assert parsed.port == 5432
    assert parsed.path == "/reprocheck"
