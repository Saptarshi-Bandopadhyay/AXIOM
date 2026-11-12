"""Integration test configuration and database initialization fixtures."""

import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from app.config import get_settings
from app.models import Base

_tables_initialized = False


@pytest.fixture(scope="function", autouse=True)
async def ensure_test_database_tables() -> None:
    """Ensure database schema is created before integration tests run."""
    global _tables_initialized
    if _tables_initialized:
        return

    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        _tables_initialized = True
    except Exception as exc:
        print(f"Notice: Automated table creation encountered: {exc}")
    finally:
        await engine.dispose()
