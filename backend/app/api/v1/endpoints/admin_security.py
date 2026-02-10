"""
Admin Security Endpoints — управление системой безопасности.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_superuser, get_db
from app.core import error_messages as em
from app.core.redis import get_redis
from app.core.time_constants import REDIS_SCAN_COUNT
from app.models import User
from app.services.security_monitor import get_security_detector

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
    ban_ttl: int | None = None
    strikes: list[StrikeDetail]


class SecurityStatsResponse(BaseModel):
    """Статистика безопасности."""
    total_bans: int
    active_bans: int
    strikes_today: int
    top_attack_types: dict


class ClearStrikesRequest(BaseModel):
    """Запрос на очистку страйков."""
    identifier: str  # "ip:1.2.3.4" или "user:uuid"
    reason: str | None = None


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


@router.get("/security/bans", response_model=list[SecurityStrikesResponse])
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
        cursor, keys = await redis.scan(cursor, match="sec:ban:*", count=REDIS_SCAN_COUNT)
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
        cursor, keys = await redis.scan(cursor, match="sec:ban:*", count=REDIS_SCAN_COUNT)
        active_bans += len(keys)
        if cursor == 0:
            break

    # Считаем страйки
    cursor = 0
    total_strikes = 0
    attack_types: dict = {}

    while True:
        cursor, keys = await redis.scan(cursor, match="sec:strike_details:*", count=REDIS_SCAN_COUNT)
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


class UserInfoResponse(BaseModel):
    """Краткая информация о пользователе для идентификации."""
    user_id: str
    full_name: str
    group_name: str | None = None
    username: str | None = None
    telegram_id: int | None = None


@router.get("/security/user/{user_id}", response_model=UserInfoResponse)
async def get_user_info_for_security(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
):
    """Получить информацию о пользователе по UUID для идентификации в таблице банов."""
    from sqlalchemy import select

    from app.models import Group

    try:
        from uuid import UUID
        uuid_obj = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=em.INVALID_UUID_FORMAT)

    result = await db.execute(select(User).where(User.id == uuid_obj))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail=em.USER_NOT_FOUND)

    group_name = None
    if user.group_id:
        group_result = await db.execute(select(Group).where(Group.id == user.group_id))
        group = group_result.scalar_one_or_none()
        if group:
            group_name = group.name

    return UserInfoResponse(
        user_id=str(user.id),
        full_name=user.full_name,
        group_name=group_name,
        username=user.username,
        telegram_id=user.telegram_id,
    )
