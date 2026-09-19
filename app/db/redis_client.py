"""Redis cache client manager."""

from typing import Optional
import redis.asyncio as aioredis
from app.config import get_settings

_redis_pool: Optional[aioredis.Redis] = None


def get_redis() -> aioredis.Redis:
    """Get or initialize the async Redis connection."""
    global _redis_pool
    if _redis_pool is None:
        settings = get_settings()
        _redis_pool = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )
    return _redis_pool


async def close_redis() -> None:
    """Graceful shutdown for Redis."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None
