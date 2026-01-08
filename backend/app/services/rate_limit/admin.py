"""
Админские функции для управления rate limit банами.
"""
import logging
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, update, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.models.user import User

from .constants import REDIS_BAN, REDIS_429_COUNT
from .models import RateLimitWarning
from .schemas import WarningRecord, WarningListResponse, ActiveBanInfo

logger = logging.getLogger(__name__)


async def get_active_bans(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
) -> WarningListResponse:
    """Получить список активных банов."""
    now = datetime.utcnow()
    
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
    
    # Получаем имена пользователей
    user_ids = [w.user_id for w in warnings if w.user_id]
    users_map = {}
    if user_ids:
        users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        users_map = {u.id: u.full_name for u in users_result.scalars().all()}
    
    items = [
        WarningRecord(
            id=w.id,
            user_id=w.user_id,
            user_name=users_map.get(w.user_id) if w.user_id else None,
            ip_address=w.ip_address,
            warning_level=w.warning_level,
            violation_count=w.violation_count,
            message=w.message,
            ban_until=w.ban_until,
            unbanned_at=w.unbanned_at,
            admin_notified=w.admin_notified,
            created_at=w.created_at,
        )
        for w in warnings
    ]
    
    return WarningListResponse(items=items, total=total)


async def get_warnings_history(
    db: AsyncSession,
    user_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
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
    
    # Получаем имена пользователей
    user_ids = [w.user_id for w in warnings if w.user_id]
    users_map = {}
    if user_ids:
        users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        users_map = {u.id: u.full_name for u in users_result.scalars().all()}
    
    items = [
        WarningRecord(
            id=w.id,
            user_id=w.user_id,
            user_name=users_map.get(w.user_id) if w.user_id else None,
            ip_address=w.ip_address,
            warning_level=w.warning_level,
            violation_count=w.violation_count,
            message=w.message,
            ban_until=w.ban_until,
            unbanned_at=w.unbanned_at,
            admin_notified=w.admin_notified,
            created_at=w.created_at,
        )
        for w in warnings
    ]
    
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
    warning.unbanned_at = datetime.utcnow()
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
    now = datetime.utcnow()
    
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
