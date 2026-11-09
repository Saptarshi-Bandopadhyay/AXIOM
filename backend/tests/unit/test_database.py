"""Unit tests for SQLAlchemy 2.0 async engine, sessionmaker, and base models."""

from unittest.mock import AsyncMock, MagicMock
import pytest
from sqlalchemy import Integer, String
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import (
    async_session_factory,
    check_db_connection,
    engine,
    get_db,
)
from app.models.base import Base, TimestampMixin


class DummyModel(Base, TimestampMixin):
    """Temporary model to verify DeclarativeBase and TimestampMixin behavior."""

    __tablename__ = "test_dummy_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)


def test_base_model_and_timestamp_mixin() -> None:
    """Verify that Base registers tables and TimestampMixin provides timestamp columns."""
    assert "test_dummy_items" in Base.metadata.tables
    table = Base.metadata.tables["test_dummy_items"]
    assert "created_at" in table.columns
    assert "updated_at" in table.columns
    assert table.columns["created_at"].nullable is False
    assert table.columns["updated_at"].nullable is False


def test_engine_and_session_factory_configuration() -> None:
    """Verify async engine dialect and sessionmaker settings."""
    assert isinstance(engine, AsyncEngine)
    assert engine.dialect.name == "postgresql"
    assert engine.dialect.driver == "asyncpg"

    assert isinstance(async_session_factory, async_sessionmaker)
    assert async_session_factory.kw.get("expire_on_commit") is False


async def test_check_db_connection_success() -> None:
    """Verify check_db_connection returns True when test query succeeds."""
    mock_engine = MagicMock(spec=AsyncEngine)
    mock_conn = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar.return_value = 1

    mock_conn.execute.return_value = mock_result
    mock_engine.connect.return_value.__aenter__.return_value = mock_conn

    is_connected = await check_db_connection(target_engine=mock_engine)
    assert is_connected is True


async def test_check_db_connection_failure() -> None:
    """Verify check_db_connection returns False when database is unreachable."""
    mock_engine = MagicMock(spec=AsyncEngine)
    mock_engine.connect.side_effect = ConnectionRefusedError("Database unreachable")

    is_connected = await check_db_connection(target_engine=mock_engine)
    assert is_connected is False


async def test_get_db_yields_session_and_handles_commit() -> None:
    """Verify get_db dependency lifecycle commits on completion."""
    mock_session = AsyncMock()
    mock_factory = MagicMock(return_value=AsyncMock())
    mock_factory.return_value.__aenter__.return_value = mock_session

    import app.core.database as db_module
    original_factory = db_module.async_session_factory
    try:
        db_module.async_session_factory = mock_factory
        generator = get_db()
        session = await anext(generator)
        assert session is mock_session

        # Finish generator normally
        with pytest.raises(StopAsyncIteration):
            await anext(generator)

        mock_session.commit.assert_awaited_once()
        mock_session.close.assert_awaited_once()
    finally:
        db_module.async_session_factory = original_factory
