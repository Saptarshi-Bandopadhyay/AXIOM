"""Tests for database engine configuration."""

from app.core.database import async_session_factory, engine


def test_database_engine_config() -> None:
    assert engine.dialect.name == "postgresql"
    assert engine.dialect.driver == "asyncpg"
    assert async_session_factory.kw.get("expire_on_commit") is False
