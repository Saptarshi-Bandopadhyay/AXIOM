"""Unit tests for database engine and session factory configuration."""

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from app.core.database import async_session_factory, engine


def test_database_engine_uses_asyncpg() -> None:
    """Verify that the database engine is configured for PostgreSQL with asyncpg."""
    assert isinstance(engine, AsyncEngine)
    assert engine.dialect.name == "postgresql"
    assert engine.dialect.driver == "asyncpg"


def test_session_factory_configuration() -> None:
    """Verify sessionmaker disables expire_on_commit for async operations."""
    assert isinstance(async_session_factory, async_sessionmaker)
    assert async_session_factory.kw.get("expire_on_commit") is False
