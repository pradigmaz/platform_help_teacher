"""
Админские функции для управления rate limit банами.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.models.user import User

from .constants import REDIS_429_COUNT, REDIS_BAN
from .models import RateLimitWarning
from .schemas import WarningListResponse, WarningRecord

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _warning_to_record(warning: RateLimitWarning, users_map: dict[UUID, str]) -> WarningRecord:
    return WarningRecord(
        id=warning.id,
        user_id=warning.user_id,
        user_name=users_map.get(warning.user_id) if warning.user_id else None,
        ip_address=warning.ip_address,
        warning_level=warning.warning_level,
        violation_count=warning.violation_count,
        message=warning.message,
        ban_until=warning.ban_until,
        unbanned_at=warning.unbanned_at,
        admin_notified=warning.admin_notified,
        created_at=warning.created_at,
    )


async def _load_user_names(db: AsyncSession, warnings: list[RateLimitWarning]) -> dict[UUID, str]:
    user_ids = [warning.user_id for warning in warnings if warning.user_id is not None]
    if not user_ids:
        return {}

    users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    return {user.id: user.full_name for user in users_result.scalars().all()}


async def get_active_bans(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
) -> WarningListResponse:
    """Получить список активных банов."""
    now = _utc_now()

    # Запрос активных банов
    query = (
        select(RateLimitWarning)
        .where(
            and_(
                RateLimitWarning.ban_until > now,
                RateLimitWarning.unbanned_at.is_(None),
            )
        )
        .order_by(desc(RateLimitWarning.created_at))
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)
    warnings = result.scalars().all()

    # Подсчёт общего количества
    count_query = select(func.count(RateLimitWarning.id)).where(
        and_(
            RateLimitWarning.ban_until > now,
            RateLimitWarning.unbanned_at.is_(None),
        )
    )
    total = await db.scalar(count_query) or 0

    users_map = await _load_user_names(db, list(warnings))
    items = [_warning_to_record(warning, users_map) for warning in warnings]

    return WarningListResponse(items=items, total=total)


async def get_warnings_history(
    db: AsyncSession,
    user_id: UUID | None = None,
    ip_address: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> WarningListResponse:
    """Получить историю предупреждений."""
    query = select(RateLimitWarning).order_by(desc(RateLimitWarning.created_at))
    count_query = select(func.count(RateLimitWarning.id))

    if user_id:
        query = query.where(RateLimitWarning.user_id == user_id)
        count_query = count_query.where(RateLimitWarning.user_id == user_id)

    if ip_address:
        query = query.where(RateLimitWarning.ip_address == ip_address)
        count_query = count_query.where(RateLimitWarning.ip_address == ip_address)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    warnings = result.scalars().all()
    total = await db.scalar(count_query) or 0

    users_map = await _load_user_names(db, list(warnings))
    items = [_warning_to_record(warning, users_map) for warning in warnings]

    return WarningListResponse(items=items, total=total)


async def unban_by_warning_id(
    db: AsyncSession,
    warning_id: UUID,
    admin_id: UUID,
    reason: str,
) -> bool:
    """Разбанить по ID предупреждения."""
    warning = await db.get(RateLimitWarning, warning_id)
    if not warning:
        return False

    # Обновляем запись в БД
    warning.unbanned_at = _utc_now()
    warning.unbanned_by = admin_id
    warning.unban_reason = reason

    # Удаляем бан из Redis
    redis = await get_redis()
    if redis:
        # По IP
        ban_key = REDIS_BAN.format(identifier=f"ip:{warning.ip_address}")
        await redis.delete(ban_key)

        # По user_id если есть
        if warning.user_id:
            ban_key = REDIS_BAN.format(identifier=f"user:{warning.user_id}")
            await redis.delete(ban_key)

        # Сбрасываем счётчик нарушений
        count_key = REDIS_429_COUNT.format(identifier=f"ip:{warning.ip_address}")
        await redis.delete(count_key)
        if warning.user_id:
            count_key = REDIS_429_COUNT.format(identifier=f"user:{warning.user_id}")
            await redis.delete(count_key)

    await db.commit()

    logger.info(f"User unbanned: warning_id={warning_id}, by_admin={admin_id}, reason={reason}")
    return True


async def unban_by_user_id(
    db: AsyncSession,
    user_id: UUID,
    admin_id: UUID,
    reason: str,
) -> int:
    """Разбанить все активные баны пользователя."""
    now = _utc_now()

    # Находим активные баны
    result = await db.execute(
        select(RateLimitWarning).where(
            and_(
                RateLimitWarning.user_id == user_id,
                RateLimitWarning.ban_until > now,
                RateLimitWarning.unbanned_at.is_(None),
            )
        )
    )
    warnings = result.scalars().all()

    count = 0
    for warning in warnings:
        warning.unbanned_at = now
        warning.unbanned_by = admin_id
        warning.unban_reason = reason
        count += 1

    # Удаляем из Redis
    redis = await get_redis()
    if redis:
        ban_key = REDIS_BAN.format(identifier=f"user:{user_id}")
        await redis.delete(ban_key)
        count_key = REDIS_429_COUNT.format(identifier=f"user:{user_id}")
        await redis.delete(count_key)

    await db.commit()

    logger.info(f"User {user_id} unbanned: {count} bans cleared by admin {admin_id}")
    return count
