"""Prompt and LLM response caching with Redis and in-memory fallback.

Computes deterministic SHA-256 cache keys from model parameters and prompt messages.
Gracefully falls back to an in-memory dictionary if Redis is offline.
"""

import hashlib
import json
import time
from typing import Any
import redis.asyncio as aioredis
from app.config import get_settings

settings = get_settings()

# In-memory fallback cache: key -> (value, expire_at_timestamp)
_memory_cache: dict[str, tuple[str, float]] = {}


def compute_cache_key(model: str, messages: list[dict[str, Any]], **kwargs: Any) -> str:
    """Compute a deterministic SHA-256 cache key for an LLM invocation.

    Args:
        model: Target model identifier (e.g., 'gemini/gemini-1.5-flash').
        messages: Conversation messages list.
        kwargs: Additional model parameters such as temperature.

    Returns:
        str: 64-character SHA-256 hexadecimal hash string.
    """
    serialized_payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "params": sorted(kwargs.items()),
        },
        sort_keys=True,
    )
    return hashlib.sha256(serialized_payload.encode("utf-8")).hexdigest()


class CacheService:
    """Async caching service with Redis and in-memory fallback."""

    def __init__(self, redis_url: str | None = None) -> None:
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis_client: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis | None:
        """Lazily initialize and return Redis client if reachable."""
        if self._redis_client is None:
            try:
                client = aioredis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=0.5,
                )
                await client.ping()
                self._redis_client = client
            except Exception:
                self._redis_client = None

        return self._redis_client

    async def get(self, key: str) -> str | None:
        """Retrieve cached string response by key.

        Args:
            key: Cache key.

        Returns:
            str | None: Cached response or None if not found or expired.
        """
        # Try Redis first
        client = await self._get_redis()
        if client:
            try:
                return await client.get(key)
            except Exception:
                pass

        # Fallback to in-memory store
        if key in _memory_cache:
            value, expire_at = _memory_cache[key]
            if time.time() < expire_at:
                return value
            del _memory_cache[key]

        return None

    async def set(self, key: str, value: str, ttl_seconds: int = 86400) -> None:
        """Store response in cache with time-to-live.

        Args:
            key: Cache key.
            value: String response to cache.
            ttl_seconds: Cache expiration time in seconds (default 24 hours).
        """
        # Try Redis first
        client = await self._get_redis()
        if client:
            try:
                await client.set(key, value, ex=ttl_seconds)
                return
            except Exception:
                pass

        # Fallback to in-memory store
        _memory_cache[key] = (value, time.time() + ttl_seconds)

    async def clear(self) -> None:
        """Clear both in-memory and Redis caches (primarily used in tests)."""
        _memory_cache.clear()
        client = await self._get_redis()
        if client:
            try:
                await client.flushdb()
            except Exception:
                pass


# Singleton cache service instance
cache_service = CacheService()
