"""
Админские функции для управления rate limit банами.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .admin_redis import clear_user_unban_side_effects, clear_warning_unban_side_effects
from .admin_repository import (
    count_active_bans,
    count_warnings_history,
    fetch_active_bans,
    fetch_active_bans_for_user,
    fetch_warnings_history,
    get_warning_by_id,
    load_user_names,
)
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


async def _build_warning_list_response(
    db: AsyncSession,
    warnings: list[RateLimitWarning],
    *,
    total: int,
) -> WarningListResponse:
    users_map = await load_user_names(db, warnings)
    items = [_warning_to_record(warning, users_map) for warning in warnings]
    return WarningListResponse(items=items, total=total)


async def get_active_bans(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
) -> WarningListResponse:
    """Получить список активных банов."""
    now = _utc_now()
    warnings = await fetch_active_bans(db, now=now, skip=skip, limit=limit)
    total = await count_active_bans(db, now=now)
    return await _build_warning_list_response(db, warnings, total=total)


async def get_warnings_history(
    db: AsyncSession,
    user_id: UUID | None = None,
    ip_address: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> WarningListResponse:
    """Получить историю предупреждений."""
    warnings = await fetch_warnings_history(
        db,
        user_id=user_id,
        ip_address=ip_address,
        skip=skip,
        limit=limit,
    )
    total = await count_warnings_history(db, user_id=user_id, ip_address=ip_address)
    return await _build_warning_list_response(db, warnings, total=total)


async def unban_by_warning_id(
    db: AsyncSession,
    warning_id: UUID,
    admin_id: UUID,
    reason: str,
) -> bool:
    """Разбанить по ID предупреждения."""
    warning = await get_warning_by_id(db, warning_id)
    if not warning:
        return False

    warning.unbanned_at = _utc_now()
    warning.unbanned_by = admin_id
    warning.unban_reason = reason

    await clear_warning_unban_side_effects(warning)
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
    warnings = await fetch_active_bans_for_user(db, user_id=user_id, now=now)

    count = 0
    for warning in warnings:
        warning.unbanned_at = now
        warning.unbanned_by = admin_id
        warning.unban_reason = reason
        count += 1

    await clear_user_unban_side_effects(user_id)
    await db.commit()

    logger.info(f"User {user_id} unbanned: {count} bans cleared by admin {admin_id}")
    return count
