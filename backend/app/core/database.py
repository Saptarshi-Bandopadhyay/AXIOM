"""Database connection engine and session management for ReproCheck."""

from collections.abc import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from app.config import get_settings

settings = get_settings()

# In testing and development, NullPool prevents asyncpg connections from binding to stale event loops
engine_kwargs: dict = {"echo": settings.DB_ECHO}
if settings.APP_ENV in ("testing", "development"):
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_pre_ping"] = True

# Asynchronous engine bound to asyncpg driver
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

# Asynchronous session factory for request-scoped database sessions
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider yielding an asynchronous database session."""
    async with async_session_factory() as session:
        yield session


async def check_db_connection(target_engine: AsyncEngine | None = None) -> bool:
    """Verify PostgreSQL connectivity by executing a SELECT 1 ping query."""
    eng = target_engine or engine
    try:
        async with eng.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception:
        return False
