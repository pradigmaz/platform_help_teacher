import pytest_asyncio

from app.core.redis import close_redis
from app.db.session import engine


@pytest_asyncio.fixture(autouse=True)
async def reset_integration_pools():
    """Keep asyncpg/redis pools bound to the current pytest event loop only."""
    await close_redis()
    await engine.dispose()
    yield
    await close_redis()
    await engine.dispose()
