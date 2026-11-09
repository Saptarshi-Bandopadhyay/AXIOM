"""Database connection engine and session management for ReproCheck.

Configures the SQLAlchemy 2.0 asynchronous engine (asyncpg), connection pool,
sessionmaker, and dependency injection helpers for FastAPI route handlers.
"""

from collections.abc import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.config import get_settings

# Retrieve current application settings
settings = get_settings()

# Create SQLAlchemy asynchronous engine bound to asyncpg driver
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    future=True,
    pool_pre_ping=True,  # Test connection health before acquiring from pool
    pool_size=10,        # Base connection pool size
    max_overflow=20,     # Maximum transient overflow connections
)

# Configure asynchronous session maker
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevent expired attributes after commit in async contexts
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider yielding an asynchronous SQLAlchemy database session.

    Ensures transactions are safely closed and rolled back on unhandled exceptions.

    Yields:
        AsyncSession: Active asynchronous database session.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connection(target_engine: AsyncEngine | None = None) -> bool:
    """Verify connectivity to PostgreSQL by executing a test ping query.

    Args:
        target_engine: Optional engine to test; defaults to global application engine.

    Returns:
        bool: True if query executes successfully, False on connection failure.
    """
    eng = target_engine or engine
    try:
        async with eng.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception:
        return False
