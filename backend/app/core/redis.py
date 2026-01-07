from redis import asyncio as aioredis
from app.core.config import settings

redis_pool = None


async def get_redis() -> aioredis.Redis:
    """Get async Redis connection pool."""
    global redis_pool
    if redis_pool is None:
        # Build URL with SSL scheme if needed
        url = settings.REDIS_URL
        if settings.REDIS_SSL and url.startswith("redis://"):
            url = url.replace("redis://", "rediss://", 1)
        
        redis_pool = aioredis.ConnectionPool.from_url(
            url,
            password=settings.REDIS_PASSWORD,
            max_connections=20,
            decode_responses=True,
        )
    return aioredis.Redis(connection_pool=redis_pool)

async def close_redis():
    """Close Redis connection pool."""
    global redis_pool
    if redis_pool:
        await redis_pool.disconnect()
        redis_pool = None