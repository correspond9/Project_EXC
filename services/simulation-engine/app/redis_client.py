import redis.asyncio as aioredis

from .config import settings

_pool: aioredis.Redis | None = None


def get_redis_pool() -> aioredis.Redis:
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=False,
            socket_keepalive=True,
        )
    return _pool


async def close_redis_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None
