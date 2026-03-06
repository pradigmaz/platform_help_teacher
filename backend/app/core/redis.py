from redis import asyncio as aioredis

from app.core.config import settings
from app.core.time_constants import (
    REDIS_HEALTH_CHECK_INTERVAL_SECONDS,
    REDIS_MAX_CONNECTIONS,
    REDIS_SOCKET_CONNECT_TIMEOUT_SECONDS,
    REDIS_SOCKET_TIMEOUT_SECONDS,
)

import logging

logger = logging.getLogger(__name__)

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
            max_connections=REDIS_MAX_CONNECTIONS,
            decode_responses=True,
            socket_timeout=REDIS_SOCKET_TIMEOUT_SECONDS,
            socket_connect_timeout=REDIS_SOCKET_CONNECT_TIMEOUT_SECONDS,
            retry_on_timeout=True,
            health_check_interval=REDIS_HEALTH_CHECK_INTERVAL_SECONDS,
        )
        logger.info(
            f"[Redis:init] Pool created with max_connections={REDIS_MAX_CONNECTIONS}, "
            f"health_check_interval={REDIS_HEALTH_CHECK_INTERVAL_SECONDS}s"
        )
    return aioredis.Redis(connection_pool=redis_pool)


async def close_redis():
    """Close Redis connection pool."""
    global redis_pool
    if redis_pool:
        await redis_pool.disconnect()
        redis_pool = None
