"""
Public API endpoints для публичных отчётов.

Без авторизации. Rate limiting для защиты от brute-force.
"""
import logging
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.limiter import limiter
from app.core.redis import get_redis
from app.schemas.report import (
    PublicReportData,
    StudentDetailData,
    PinVerifyRequest,
    PinVerifyResponse,
)
from app.services.reports import ReportService
from app.services.pin_service import report_pin_service, PIN_LOCKOUT_SECONDS

from .public_reports_helpers import (
    get_client_ip,
    get_valid_report,
    check_pin_session,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/report/{code}", response_model=PublicReportData)
@limiter.limit("100/minute")
async def get_public_report(
    request: Request,
    code: str,
    attestation: str = "first",
    db: AsyncSession = Depends(get_db),
):
    """
    Получить данные публичного отчёта группы.

    - **code**: 8-символьный код отчёта
    - **attestation**: тип аттестации (first или second)

    Если отчёт защищён PIN-кодом, вернёт 401 с has_pin=true.
    Сначала нужно вызвать /verify-pin для получения доступа.
    """
    if attestation not in ("first", "second"):
        attestation = "first"

    report = await get_valid_report(db, code, request=request)
    client_ip = get_client_ip(request)

    await check_pin_session(report, code, client_ip)

    service = ReportService(db)
    user_agent = request.headers.get("User-Agent")
    await service.log_view(report.id, client_ip, user_agent)

    report_data = await service.get_group_report_data(report, attestation_type=attestation)

    logger.info("Public report %s viewed from %s, attestation=%s", code, client_ip, attestation)

    return report_data


@router.post("/report/{code}/verify-pin", response_model=PinVerifyResponse)
@limiter.limit("10/minute")
async def verify_report_pin(
    request: Request,
    code: str,
    pin_data: PinVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Проверить PIN-код для доступа к отчёту.

    - **code**: 8-символьный код отчёта
    - **pin**: PIN-код (4-6 цифр)

    После 5 неудачных попыток доступ блокируется на 15 минут.
    """
    report = await get_valid_report(db, code, request=request)
    client_ip = get_client_ip(request)

    lockout_remaining = await report_pin_service.check_lockout(code, client_ip)
    if lockout_remaining:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts",
            headers={"Retry-After": str(lockout_remaining)},
        )

    if not report.pin_hash:
        return PinVerifyResponse(success=True, message="No PIN required")

    service = ReportService(db)
    if service.verify_pin(pin_data.pin, report.pin_hash):
        await report_pin_service.reset_attempts(code, client_ip)

        try:
            redis = await get_redis()
            if redis:
                session_key = f"report_pin_session:{code}:{client_ip}"
                await redis.setex(session_key, 3600, "1")
        except Exception as e:
            logger.warning("Redis error creating PIN session: %s", e)

        logger.info("PIN verified for report %s from %s", code, client_ip)

        return PinVerifyResponse(success=True, message="PIN verified")

    attempts_left = await report_pin_service.increment_attempts(code, client_ip)

    logger.warning(
        "Invalid PIN attempt for report %s from %s, %s attempts left",
        code, client_ip, attempts_left,
    )

    if attempts_left == 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts",
            headers={"Retry-After": str(PIN_LOCKOUT_SECONDS)},
        )

    return PinVerifyResponse(
        success=False,
        message="Invalid PIN",
        attempts_left=attempts_left,
    )


@router.get("/report/{code}/student/{student_id}", response_model=StudentDetailData)
@limiter.limit("100/minute")
async def get_public_student_report(
    request: Request,
    code: str,
    student_id: UUID,
    attestation: str = "first",
    db: AsyncSession = Depends(get_db),
):
    """
    Получить детальные данные студента из публичного отчёта.

    - **code**: 8-символьный код отчёта
    - **attestation**: тип аттестации (first или second)
    - **student_id**: UUID студента

    Если отчёт защищён PIN-кодом, требуется предварительная верификация.
    """
    if attestation not in ("first", "second"):
        attestation = "first"

    report = await get_valid_report(db, code, request=request)
    client_ip = get_client_ip(request)

    await check_pin_session(report, code, client_ip)

    service = ReportService(db)
    student_data = await service.get_student_report_data(report, student_id, attestation)

    if not student_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found in this report",
        )

    user_agent = request.headers.get("User-Agent")
    await service.log_view(report.id, client_ip, user_agent)

    logger.info("Student %s report viewed from %s via report %s", student_id, client_ip, code)

    return student_data


@router.get("/report/{code}/check")
@limiter.limit("100/minute")
async def check_report_status(
    request: Request,
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Проверить статус отчёта (существует, активен, требует PIN).

    Используется для предварительной проверки перед отображением UI.
    """
    service = ReportService(db)
    report = await service.get_report_by_code(code, check_active=False, check_expiry=False)

    if not report:
        return {
            "exists": False,
            "active": False,
            "expired": False,
            "has_pin": False,
            "message": "Report not found",
        }

    is_expired = False
    if report.expires_at and datetime.now(timezone.utc) > report.expires_at:
        is_expired = True

    return {
        "exists": True,
        "active": report.is_active,
        "expired": is_expired,
        "has_pin": report.pin_hash is not None,
        "report_type": report.report_type,
        "message": (
            "Report expired" if is_expired
            else ("Report not available" if not report.is_active else "OK")
        ),
    }
