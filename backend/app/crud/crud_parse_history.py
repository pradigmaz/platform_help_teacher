"""
CRUD для истории парсинга
"""
from datetime import datetime
from uuid import UUID
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parse_history import ParseHistory


async def create_history(
    db: AsyncSession,
    teacher_id: UUID,
    config_id: Optional[UUID] = None
) -> ParseHistory:
    """Создать запись истории (начало парсинга)"""
    history = ParseHistory(
        teacher_id=teacher_id,
        config_id=config_id,
        status="running"
    )
    db.add(history)
    await db.flush()
    return history


async def complete_history(
    db: AsyncSession,
    history_id: UUID,
    stats: dict,
    error: Optional[str] = None
) -> Optional[ParseHistory]:
    """Завершить запись истории"""
    result = await db.execute(
        select(ParseHistory).where(ParseHistory.id == history_id)
    )
    history = result.scalar_one_or_none()
    if not history:
        return None
    
    history.finished_at = datetime.utcnow()
    history.status = "failed" if error else "success"
    history.lessons_created = stats.get("lessons_created", 0)
    history.lessons_skipped = stats.get("lessons_skipped", 0)
    history.conflicts_created = stats.get("conflicts_created", 0)
    history.error_message = error
    
    return history


async def get_history(
    db: AsyncSession,
    teacher_id: UUID,
    limit: int = 20
) -> list[ParseHistory]:
    """Получить историю парсинга"""
    result = await db.execute(
        select(ParseHistory)
        .where(ParseHistory.teacher_id == teacher_id)
        .order_by(ParseHistory.started_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_last_history(
    db: AsyncSession,
    teacher_id: UUID
) -> Optional[ParseHistory]:
    """Получить последнюю запись истории"""
    result = await db.execute(
        select(ParseHistory)
        .where(ParseHistory.teacher_id == teacher_id)
        .order_by(ParseHistory.started_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
