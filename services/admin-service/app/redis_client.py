"""Shared async Redis client for admin-service."""
import redis.asyncio as aioredis

from .config import settings

_pool: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    """Return the singleton Redis client. Initialised lazily on first call."""
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _pool
