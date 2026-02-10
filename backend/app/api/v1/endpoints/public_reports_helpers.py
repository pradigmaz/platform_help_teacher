"""
Вспомогательные функции для публичных отчётов.

Honeypot-защита, валидация отчётов, PIN-сессии.
"""
import json
import logging
from typing import Optional
from datetime import datetime, timezone

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.models.group_report import GroupReport
from app.services.reports import ReportService
from app.services.security_monitor import AttackType
from app.services.security_monitor.constants import (
    REDIS_SECURITY_BAN, BAN_DURATION,
)

logger = logging.getLogger(__name__)

# Honeypot коды — обращение к ним = мгновенный бан
HONEYPOT_CODES = {
    "AAAAAAAA", "BBBBBBBB", "CCCCCCCC", "ZZZZZZZZ",
    "12345678", "87654321", "11111111", "22222222",
    "ABCD1234", "1234ABCD", "TESTTEST", "TESTCODE",
    "ADMIN123", "PASSWORD", "QWERTY12", "ASDFGHJK",
}


def get_client_ip(request: Request) -> str:
    """Получить IP клиента с учётом прокси."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def check_honeypot(code: str, request: Request) -> None:
    """Проверка honeypot кодов — мгновенный бан при совпадении."""
    if code.upper() not in HONEYPOT_CODES:
        return

    ip = get_client_ip(request)
    logger.warning("🍯 REPORT HONEYPOT: %s tried code %s", ip, code)

    redis = await get_redis()
    if redis:
        identifier = f"ip:{ip}"
        ban_key = REDIS_SECURITY_BAN.format(identifier=identifier)
        await redis.setex(ban_key, BAN_DURATION, AttackType.HONEYPOT.value)

        details_key = f"sec:strike_details:{identifier}"
        detail = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "url": f"/public/report/{code}",
            "attack_type": AttackType.HONEYPOT.value,
            "description": "Report honeypot code triggered",
            "severity": 10,
        }
        await redis.rpush(details_key, json.dumps(detail))
        await redis.expire(details_key, BAN_DURATION)

    # 404 чтобы не палить что это ловушка
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Report not found",
    )


async def get_valid_report(
    db: AsyncSession,
    code: str,
    request: Optional[Request] = None,
) -> GroupReport:
    """
    Получить валидный отчёт по коду.

    Проверяет: honeypot, существование, активность, срок действия.
    """
    if request:
        await check_honeypot(code, request)

    service = ReportService(db)
    report = await service.get_report_by_code(code, check_active=False, check_expiry=False)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    if not report.is_active:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Report not available",
        )

    if report.expires_at and datetime.now(timezone.utc) > report.expires_at:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Report expired",
        )

    return report


async def check_pin_session(report: GroupReport, code: str, client_ip: str) -> None:
    """
    Проверить PIN-сессию для защищённого отчёта.

    Если отчёт без PIN — ничего не делает.
    Если PIN есть, но сессия невалидна — выбрасывает 401.
    """
    if not report.pin_hash:
        return

    try:
        redis = await get_redis()
        if redis:
            session_key = f"report_pin_session:{code}:{client_ip}"
            session_valid = await redis.get(session_key)

            if not session_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="PIN required",
                    headers={"X-Has-Pin": "true"},
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="PIN required",
                headers={"X-Has-Pin": "true"},
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("[PublicReports:check_pin_session] Redis error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="PIN required",
            headers={"X-Has-Pin": "true"},
        )
