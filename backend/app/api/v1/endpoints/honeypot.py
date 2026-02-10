"""
Honeypot Endpoints — ловушки для сканеров и скрипт-кидди.

Любое обращение к этим эндпоинтам = мгновенный бан.
"""

import logging

from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

from app.services.security_monitor import AttackType, get_security_detector
from app.services.security_monitor.constants import MAX_STRIKES, AttackPattern, StrikeLevel

logger = logging.getLogger(__name__)
router = APIRouter()

# Severity=10 = мгновенный бан (MAX_STRIKES=3, так что 10 > 3)
HONEYPOT_ATTACK = AttackPattern(
    pattern=None,  # type: ignore
    attack_type=AttackType.HONEYPOT,
    description="Honeypot trap triggered",
    severity=10,
)

# "Вкусные" пути для сканеров
HONEYPOT_PATHS = [
    # Админские
    "/admin/config",
    "/admin/settings",
    "/admin/database",
    "/admin/users/export",
    "/admin/dump",
    "/admin/backup/download",
    "/admin/sql",
    "/admin/shell",
    "/admin/console",
    "/admin/debug",
    # Популярные уязвимости
    "/phpMyAdmin",
    "/phpmyadmin",
    "/pma",
    "/mysql",
    "/wp-admin",
    "/wp-login.php",
    "/administrator",
    "/.env",
    "/.git/config",
    "/config.php",
    "/debug",
    "/api/debug",
    "/api/v1/debug",
    "/swagger.json",
    "/actuator",
    "/actuator/health",
    "/graphql",
    # Файлы
    "/backup.sql",
    "/dump.sql",
    "/database.sql",
    "/users.csv",
    "/passwords.txt",
]


async def _trigger_honeypot(request: Request, path: str) -> JSONResponse:
    """Срабатывание ловушки — мгновенный бан."""
    ip = _get_client_ip(request)
    detector = get_security_detector()

    logger.warning(f"🍯 HONEYPOT TRIGGERED: {ip} → {path}")

    # Записываем страйк с severity=10 (мгновенный бан)
    result = await detector.check_and_record(
        ip_address=ip,
        url=path,
        user_id=None,
        body=None,
    )

    # Если детектор не забанил (нет Redis), баним вручную
    if result.strike_level != StrikeLevel.BANNED:
        import json
        from datetime import datetime

        from app.core.redis import get_redis
        from app.services.security_monitor.constants import BAN_DURATION, REDIS_SECURITY_BAN, REDIS_STRIKE_COUNT

        redis = await get_redis()
        if redis:
            identifier = f"ip:{ip}"
            ban_key = REDIS_SECURITY_BAN.format(identifier=identifier)
            count_key = REDIS_STRIKE_COUNT.format(identifier=identifier)
            details_key = f"sec:strike_details:{identifier}"

            await redis.setex(ban_key, BAN_DURATION, AttackType.HONEYPOT.value)
            await redis.set(count_key, MAX_STRIKES + 1)
            await redis.expire(count_key, BAN_DURATION)

            detail = {
                "timestamp": datetime.utcnow().isoformat(),
                "url": path,
                "attack_type": AttackType.HONEYPOT.value,
                "description": "Honeypot trap triggered",
                "severity": 10,
            }
            await redis.rpush(details_key, json.dumps(detail))
            await redis.expire(details_key, BAN_DURATION)

    # Возвращаем фейковый ответ (чтобы не палить что это ловушка)
    return JSONResponse(
        status_code=403,
        content={"detail": "Access denied"},
    )


def _get_client_ip(request: Request) -> str:
    """Получает IP клиента."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host
    return "unknown"


# Генерируем эндпоинты для всех honeypot путей
@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def honeypot_catch_all(request: Request, path: str):
    """Ловушка для всех путей этого роутера."""
    full_path = f"/{path}"
    return await _trigger_honeypot(request, full_path)
