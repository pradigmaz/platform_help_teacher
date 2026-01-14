"""
Admin Security Endpoints — управление системой безопасности.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_superuser, get_db
from app.models import User
from app.services.security_monitor import get_security_detector, AttackType, StrikeLevel
from app.core.redis import get_redis

logger = logging.getLogger(__name__)
router = APIRouter()


# === Schemas ===

class StrikeDetail(BaseModel):
    """Детали одного страйка."""
    timestamp: str
    url: str
    attack_type: str
    description: str
    severity: int


class SecurityStrikesResponse(BaseModel):
    """Ответ со страйками пользователя/IP."""
    identifier: str
    strike_count: int
    is_banned: bool
    ban_ttl: Optional[int] = None
    strikes: List[StrikeDetail]


class SecurityStatsResponse(BaseModel):
    """Статистика безопасности."""
    total_bans: int
    active_bans: int
    strikes_today: int
    top_attack_types: dict


class ClearStrikesRequest(BaseModel):
    """Запрос на очистку страйков."""
    identifier: str  # "ip:1.2.3.4" или "user:uuid"
    reason: Optional[str] = None


class ClearStrikesResponse(BaseModel):
    """Ответ на очистку страйков."""
    success: bool
    identifier: str
    message: str


# === Endpoints ===

@router.get("/security/strikes/{identifier}", response_model=SecurityStrikesResponse)
async def get_user_strikes(
    identifier: str,
    current_user: User = Depends(get_current_active_superuser),
):
    """
    Получить страйки по идентификатору.
    
    identifier: "ip:1.2.3.4" или "user:uuid"
    """
    detector = get_security_detector()
    redis = await get_redis()
    
    count, details = await detector.get_strikes(identifier)
    
    # Проверяем бан
    is_banned = False
    ban_ttl = None
    if redis:
        ban_key = f"sec:ban:{identifier}"
        if await redis.exists(ban_key):
            is_banned = True
            ban_ttl = await redis.ttl(ban_key)
    
    return SecurityStrikesResponse(
        identifier=identifier,
        strike_count=count,
        is_banned=is_banned,
        ban_ttl=ban_ttl,
        strikes=[StrikeDetail(**d) for d in details],
    )


@router.delete("/security/strikes", response_model=ClearStrikesResponse)
async def clear_strikes(
    request: ClearStrikesRequest,
    current_user: User = Depends(get_current_active_superuser),
):
    """Очистить страйки и снять бан."""
    detector = get_security_detector()
    
    success = await detector.clear_strikes(request.identifier)
    
    if success:
        logger.info(
            f"Admin {current_user.id} cleared strikes for {request.identifier}. "
            f"Reason: {request.reason or 'not specified'}"
        )
    
    return ClearStrikesResponse(
        success=success,
        identifier=request.identifier,
        message="Страйки очищены" if success else "Ошибка очистки",
    )


@router.get("/security/bans", response_model=List[SecurityStrikesResponse])
async def list_active_bans(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_superuser),
):
    """Список активных банов по безопасности."""
    redis = await get_redis()
    if not redis:
        return []
    
    detector = get_security_detector()
    results = []
    
    # Сканируем ключи банов
    cursor = 0
    ban_keys = []
    
    while True:
        cursor, keys = await redis.scan(cursor, match="sec:ban:*", count=100)
        ban_keys.extend(keys)
        if cursor == 0:
            break
    
    # Получаем детали для каждого бана
    for key in ban_keys[skip:skip + limit]:
        identifier = key.replace("sec:ban:", "")
        count, details = await detector.get_strikes(identifier)
        ban_ttl = await redis.ttl(key)
        
        results.append(SecurityStrikesResponse(
            identifier=identifier,
            strike_count=count,
            is_banned=True,
            ban_ttl=ban_ttl,
            strikes=[StrikeDetail(**d) for d in details],
        ))
    
    return results


@router.get("/security/stats", response_model=SecurityStatsResponse)
async def get_security_stats(
    current_user: User = Depends(get_current_active_superuser),
):
    """Статистика системы безопасности."""
    redis = await get_redis()
    if not redis:
        return SecurityStatsResponse(
            total_bans=0,
            active_bans=0,
            strikes_today=0,
            top_attack_types={},
        )
    
    # Считаем активные баны
    cursor = 0
    active_bans = 0
    while True:
        cursor, keys = await redis.scan(cursor, match="sec:ban:*", count=100)
        active_bans += len(keys)
        if cursor == 0:
            break
    
    # Считаем страйки
    cursor = 0
    total_strikes = 0
    attack_types: dict = {}
    
    while True:
        cursor, keys = await redis.scan(cursor, match="sec:strike_details:*", count=100)
        for key in keys:
            details = await redis.lrange(key, 0, -1)
            total_strikes += len(details)
            
            import json
            for d in details:
                try:
                    data = json.loads(d)
                    at = data.get("attack_type", "unknown")
                    attack_types[at] = attack_types.get(at, 0) + 1
                except Exception:
                    pass
        
        if cursor == 0:
            break
    
    return SecurityStatsResponse(
        total_bans=active_bans,  # Исторические баны не храним в Redis
        active_bans=active_bans,
        strikes_today=total_strikes,  # За окно страйков (1 час)
        top_attack_types=dict(sorted(attack_types.items(), key=lambda x: -x[1])[:5]),
    )
