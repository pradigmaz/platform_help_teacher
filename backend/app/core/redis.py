from redis import asyncio as aioredis
from app.core.config import settings

# Глобальная переменная для пула
redis_pool = None

async def get_redis() -> aioredis.Redis:
    global redis_pool
    if redis_pool is None:
        redis_pool = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=10  # Ограничиваем кол-во соединений
        )
    return redis_pool

async def close_redis():
    global redis_pool
    if redis_pool:
        await redis_pool.close()