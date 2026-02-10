from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.time_constants import (
    DB_POOL_MAX_OVERFLOW,
    DB_POOL_SIZE,
    DB_POOL_TIMEOUT_SECONDS,
    DB_SYNC_POOL_MAX_OVERFLOW,
    DB_SYNC_POOL_SIZE,
)

# Async engine для FastAPI
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_POOL_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT_SECONDS,
    pool_pre_ping=True,
)

# Sync engine для Celery tasks
sync_database_url = settings.DATABASE_URL.replace("+asyncpg", "")
sync_engine = create_engine(
    sync_database_url,
    echo=False,
    pool_size=DB_SYNC_POOL_SIZE,
    max_overflow=DB_SYNC_POOL_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT_SECONDS,
    pool_pre_ping=True,
)

# Async session factory для FastAPI
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)

# Sync session factory для Celery
SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)


# Dependency для FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
