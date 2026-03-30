"""
Repository helpers for rate-limit admin flows.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.models.user import User

from .models import RateLimitWarning

warning_table = RateLimitWarning.__table__
user_table = User.__table__


def _active_ban_filters(now: datetime) -> tuple[ColumnElement[bool], ...]:
    return (
        warning_table.c.ban_until.is_not(None),
        warning_table.c.ban_until > now,
        warning_table.c.unbanned_at.is_(None),
    )


def _history_filters(
    user_id: UUID | None,
    ip_address: str | None,
) -> list[ColumnElement[bool]]:
    filters: list[ColumnElement[bool]] = []

    if user_id is not None:
        filters.append(warning_table.c.user_id == user_id)

    if ip_address is not None:
        filters.append(warning_table.c.ip_address == ip_address)

    return filters


async def fetch_active_bans(
    db: AsyncSession,
    *,
    now: datetime,
    skip: int,
    limit: int,
) -> list[RateLimitWarning]:
    query = (
        select(RateLimitWarning)
        .where(*_active_ban_filters(now))
        .order_by(desc(warning_table.c.created_at))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def count_active_bans(db: AsyncSession, *, now: datetime) -> int:
    query = select(func.count(warning_table.c.id)).where(*_active_ban_filters(now))
    return await db.scalar(query) or 0


async def fetch_warnings_history(
    db: AsyncSession,
    *,
    user_id: UUID | None,
    ip_address: str | None,
    skip: int,
    limit: int,
) -> list[RateLimitWarning]:
    query = select(RateLimitWarning).order_by(desc(warning_table.c.created_at))
    for condition in _history_filters(user_id, ip_address):
        query = query.where(condition)

    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


async def count_warnings_history(
    db: AsyncSession,
    *,
    user_id: UUID | None,
    ip_address: str | None,
) -> int:
    query = select(func.count(warning_table.c.id))
    for condition in _history_filters(user_id, ip_address):
        query = query.where(condition)

    return await db.scalar(query) or 0


async def load_user_names(db: AsyncSession, warnings: list[RateLimitWarning]) -> dict[UUID, str]:
    user_ids = list({warning.user_id for warning in warnings if warning.user_id is not None})
    if not user_ids:
        return {}

    rows = (
        await db.execute(
            select(user_table.c.id, user_table.c.full_name).where(user_table.c.id.in_(user_ids))
        )
    ).all()
    return {row.id: row.full_name for row in rows}


async def get_warning_by_id(db: AsyncSession, warning_id: UUID) -> RateLimitWarning | None:
    return await db.get(RateLimitWarning, warning_id)


async def fetch_active_bans_for_user(
    db: AsyncSession,
    *,
    user_id: UUID,
    now: datetime,
) -> list[RateLimitWarning]:
    result = await db.execute(
        select(RateLimitWarning).where(
            warning_table.c.user_id == user_id,
            *_active_ban_filters(now),
        )
    )
    return list(result.scalars().all())
