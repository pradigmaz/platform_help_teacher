import logging
import time
from typing import cast

from sqlalchemy import create_engine
from sqlalchemy import event
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

logger = logging.getLogger(__name__)

# Async engine для FastAPI
database_url = cast(str, settings.DATABASE_URL)

engine = create_async_engine(
    database_url,
    echo=False,
    future=True,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_POOL_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT_SECONDS,
    pool_pre_ping=True,
)

# Sync engine для Celery tasks
sync_database_url = database_url.replace("+asyncpg", "")
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


def _install_slow_query_logging(target_engine) -> None:
    threshold_ms = settings.SQL_SLOW_QUERY_MS
    if threshold_ms <= 0:
        return

    @event.listens_for(target_engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # type: ignore[no-untyped-def]
        context._query_start_time = time.perf_counter()

    @event.listens_for(target_engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # type: ignore[no-untyped-def]
        start_time = getattr(context, "_query_start_time", None)
        if start_time is None:
            return

        duration_ms = (time.perf_counter() - start_time) * 1000
        if duration_ms < threshold_ms:
            return

        compact_sql = " ".join(statement.split())
        logger.warning(
            "slow_sql duration_ms=%.1f threshold_ms=%s sql=%s",
            duration_ms,
            threshold_ms,
            compact_sql[:400],
        )


_install_slow_query_logging(engine.sync_engine)
_install_slow_query_logging(sync_engine)


# Dependency для FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
