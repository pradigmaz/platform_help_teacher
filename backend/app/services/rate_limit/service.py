"""
Сервис управления rate limit предупреждениями.
"""
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, Set
from uuid import UUID

from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.models.user import User, UserRole

from .constants import (
    WarningLevel, THRESHOLDS, COUNT_WINDOW,
    REDIS_429_COUNT, REDIS_BAN, REDIS_WARNING_SENT, MESSAGES
)
from .models import RateLimitWarning
from .schemas import WarningResponse, ActiveBanInfo

logger = logging.getLogger(__name__)

# Кэш админских user_id (обновляется при старте и периодически)
_admin_user_ids: Set[UUID] = set()
_admin_cache_loaded: bool = False

# Singleton instance
_service: Optional["RateLimitService"] = None


def get_rate_limit_service() -> "RateLimitService":
    """Получить singleton сервиса."""
    global _service
    if _service is None:
        _service = RateLimitService()
    return _service


async def load_admin_ids_from_db(db: AsyncSession) -> None:
    """Загрузить ID админов из БД в кэш."""
    global _admin_user_ids, _admin_cache_loaded
    try:
        result = await db.execute(
            select(User.id).where(User.role == UserRole.ADMIN)
        )
        _admin_user_ids = {row[0] for row in result.fetchall()}
        _admin_cache_loaded = True
        logger.info(f"Loaded {len(_admin_user_ids)} admin IDs for rate limit bypass")
    except Exception as e:
        logger.error(f"Failed to load admin IDs: {e}")


def is_admin_user(user_id: Optional[UUID]) -> bool:
    """Проверить, является ли user_id админом (из кэша)."""
    if not user_id:
        return False
    return user_id in _admin_user_ids


class RateLimitService:
    """Сервис rate limit с мягкими предупреждениями."""
    
    def _hash_fingerprint(self, fingerprint: dict) -> str:
        """Хеширует fingerprint для использования как ключ."""
        import json
        fp_str = json.dumps(fingerprint, sort_keys=True)
        return hashlib.sha256(fp_str.encode()).hexdigest()[:16]
    
    async def check_ban(
        self,
        ip_address: str,
        user_id: Optional[UUID] = None,
        fingerprint: Optional[dict] = None,
    ) -> ActiveBanInfo:
        """Проверяет, забанен ли пользователь."""
        # Админы не банятся
        if is_admin_user(user_id):
            return ActiveBanInfo(is_banned=False)
        
        redis = await get_redis()
        if not redis:
            return ActiveBanInfo(is_banned=False)
        
        # Проверяем бан по IP
        ban_key = REDIS_BAN.format(identifier=f"ip:{ip_address}")
        ban_data = await redis.get(ban_key)
        
        if ban_data:
            ttl = await redis.ttl(ban_key)
            ban_until = datetime.utcnow() + timedelta(seconds=ttl) if ttl > 0 else None
            return ActiveBanInfo(
                is_banned=True,
                ban_until=ban_until,
                warning_level=WarningLevel.SOFT_BAN if ttl <= 600 else WarningLevel.HARD_BAN,
                message=MESSAGES.get(WarningLevel.SOFT_BAN if ttl <= 600 else WarningLevel.HARD_BAN),
            )
        
        # Проверяем бан по user_id
        if user_id:
            ban_key = REDIS_BAN.format(identifier=f"user:{user_id}")
            ban_data = await redis.get(ban_key)
            if ban_data:
                ttl = await redis.ttl(ban_key)
                ban_until = datetime.utcnow() + timedelta(seconds=ttl) if ttl > 0 else None
                return ActiveBanInfo(
                    is_banned=True,
                    ban_until=ban_until,
                    warning_level=WarningLevel.SOFT_BAN if ttl <= 600 else WarningLevel.HARD_BAN,
                    message=MESSAGES.get(WarningLevel.SOFT_BAN if ttl <= 600 else WarningLevel.HARD_BAN),
                )
        
        return ActiveBanInfo(is_banned=False)
    
    async def record_violation(
        self,
        ip_address: str,
        user_id: Optional[UUID] = None,
        fingerprint: Optional[dict] = None,
    ) -> Tuple[WarningLevel, Optional[str]]:
        """
        Записывает нарушение (429 ошибку) и возвращает уровень предупреждения.
        
        Returns:
            (level, message) — уровень и сообщение для пользователя
        """
        # Админы не получают предупреждений и банов
        if is_admin_user(user_id):
            return WarningLevel.NONE, None
        
        redis = await get_redis()
        if not redis:
            return WarningLevel.NONE, None
        
        # Идентификатор для подсчёта
        identifier = f"ip:{ip_address}"
        if user_id:
            identifier = f"user:{user_id}"
        
        # Инкрементируем счётчик
        count_key = REDIS_429_COUNT.format(identifier=identifier)
        count = await redis.incr(count_key)
        
        if count == 1:
            await redis.expire(count_key, COUNT_WINDOW)
        
        # Определяем уровень по порогам
        level = WarningLevel.NONE
        threshold = None
        
        for t in THRESHOLDS:
            if count >= t.count:
                level = t.level
                threshold = t
        
        if level == WarningLevel.NONE:
            return level, None
        
        message = MESSAGES.get(level)
        
        # Проверяем, отправляли ли уже предупреждение этого уровня
        warn_key = REDIS_WARNING_SENT.format(identifier=f"{identifier}:{level.value}")
        already_warned = await redis.exists(warn_key)
        
        if not already_warned and threshold:
            # Помечаем что предупреждение отправлено
            await redis.setex(warn_key, COUNT_WINDOW, "1")
            
            # Если нужен бан — устанавливаем
            if threshold.ban_duration > 0:
                ban_key = REDIS_BAN.format(identifier=identifier)
                await redis.setex(ban_key, threshold.ban_duration, level.value)
                logger.warning(
                    f"Rate limit ban: {identifier}, level={level.value}, "
                    f"duration={threshold.ban_duration}s, violations={count}"
                )
            
            return level, message
        
        # Уже предупреждали — не спамим
        return level, None
