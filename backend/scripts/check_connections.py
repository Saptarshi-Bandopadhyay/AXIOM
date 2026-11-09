"""Utility script to verify local PostgreSQL and Redis connectivity.

This script checks connection status for:
1. PostgreSQL (via DATABASE_URL using asyncpg / sqlalchemy)
2. Redis (via REDIS_URL using redis-py)

Usage:
    uv run python scripts/check_connections.py
"""

import asyncio
import os
import sys
from urllib.parse import urlparse

# Ensure app package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


async def check_postgres(database_url: str) -> bool:
    """Check connectivity to PostgreSQL database.

    Args:
        database_url: SQLAlchemy-format database connection string.

    Returns:
        bool: True if connection succeeded, False otherwise.
    """
    print(f"[PostgreSQL] Checking connection to {database_url}...")
    try:
        import asyncpg

        # Parse connection parameters from URL
        parsed = urlparse(database_url.replace("postgresql+asyncpg://", "postgresql://"))
        user = parsed.username or "postgres"
        password = parsed.password or ""
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 5432
        database = parsed.path.lstrip("/") or "reprocheck"

        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database,
            timeout=5.0,
        )
        version = await conn.fetchval("SELECT version();")
        await conn.close()
        print(f"[PostgreSQL] SUCCESS: Connected to {database} on {host}:{port}")
        print(f"             Server: {version.split(',')[0]}")
        return True
    except Exception as e:
        print(f"[PostgreSQL] FAILED: Could not connect to database.")
        print(f"             Details: {e}")
        return False


async def check_redis(redis_url: str) -> bool:
    """Check connectivity to Redis cache server.

    Args:
        redis_url: Redis connection string (e.g., redis://localhost:6379/0).

    Returns:
        bool: True if ping was successful, False otherwise.
    """
    print(f"[Redis] Checking connection to {redis_url}...")
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(redis_url, socket_timeout=3.0)
        pong = await client.ping()
        await client.aclose()
        if pong:
            print(f"[Redis] SUCCESS: Connected and received PONG from Redis.")
            return True
        return False
    except Exception as e:
        print(f"[Redis] WARNING: Could not connect to Redis at {redis_url}.")
        print(f"        Details: {e}")
        print("        Note: In-memory fallback will be used if Redis is not running locally.")
        return False


async def main() -> None:
    """Run connection checks for all configured backing services."""
    from dotenv import load_dotenv

    load_dotenv()

    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/reprocheck",
    )
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    print("=" * 60)
    print("ReproCheck Backing Services Connectivity Check")
    print("=" * 60)

    pg_ok = await check_postgres(db_url)
    print("-" * 60)
    redis_ok = await check_redis(redis_url)
    print("=" * 60)

    if pg_ok and redis_ok:
        print("ALL CHECKS PASSED: PostgreSQL and Redis are ready.")
    elif pg_ok and not redis_ok:
        print("PARTIAL PASS: PostgreSQL is connected. Redis is unavailable.")
        print("(Application can run with in-memory caching fallback.)")
    else:
        print("ACTION REQUIRED: PostgreSQL connection failed.")
        print("Verify your credentials in backend/.env or start PostgreSQL.")


if __name__ == "__main__":
    asyncio.run(main())
