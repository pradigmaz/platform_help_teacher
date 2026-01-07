"""
Public API endpoints для публичных отчётов.

Без авторизации. Rate limiting для защиты от brute-force.
"""
import logging
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.limiter import limiter
from app.models.group_report import GroupReport
from app.schemas.report import (
    PublicReportData,
    StudentDetailData,
    PinVerifyRequest,
    PinVerifyResponse,
)
from app.services.reports import ReportService
from app.services.pin_service import report_pin_service

logger = logging.getLogger(__name__)

router = APIRouter()


async def _get_valid_report(
    db: AsyncSession,
    code: str,
    check_pin: bool = False,
    request: Optional[Request] = None
) -> GroupReport:
    """
    Получить валидный отчёт по коду.
    
    Проверяет:
    - Существование отчёта
    - Активность отчёта
    - Срок действия
    """
    service = ReportService(db)
    report = await service.get_report_by_code(code, check_active=False, check_expiry=False)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Проверка активности
    if not report.is_active:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Report not available"
        )
    
    # Проверка срока действия
    if report.expires_at and datetime.now(timezone.utc) > report.expires_at:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Report expired"
        )
    
    return report


def _get_client_ip(request: Request) -> str:
    """Получить IP клиента."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.get("/report/{code}", response_model=PublicReportData)
@limiter.limit("100/minute")
async def get_public_report(
    request: Request,
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Получить данные публичного отчёта группы.
    
    - **code**: 8-символьный код отчёта
    
    Если отчёт защищён PIN-кодом, вернёт 401 с has_pin=true.
    Сначала нужно вызвать /verify-pin для получения доступа.
    """
    report = await _get_valid_report(db, code, request=request)
    client_ip = _get_client_ip(request)
    
    # Проверка PIN-защиты
    if report.pin_hash:
        # Проверяем, есть ли валидная сессия PIN
        try:
            redis = await get_redis()
            if redis:
                session_key = f"report_pin_session:{code}:{client_ip}"
                session_valid = await redis.get(session_key)
                
                if not session_valid:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="PIN required",
                        headers={"X-Has-Pin": "true"}
                    )
            else:
                # Без Redis не можем проверить сессию - требуем PIN
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="PIN required",
                    headers={"X-Has-Pin": "true"}
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Redis error checking PIN session: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="PIN required",
                headers={"X-Has-Pin": "true"}
            )
    
    # Логируем просмотр
    service = ReportService(db)
    user_agent = request.headers.get("User-Agent")
    await service.log_view(report.id, client_ip, user_agent)
    
    # Собираем данные
    report_data = await service.get_group_report_data(report)
    
    logger.info(f"Public report {code} viewed from {client_ip}")
    
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
    report = await _get_valid_report(db, code, request=request)
    client_ip = _get_client_ip(request)
    
    # Проверка блокировки
    lockout_remaining = await report_pin_service.check_lockout(code, client_ip)
    if lockout_remaining:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts",
            headers={"Retry-After": str(lockout_remaining)}
        )
    
    # Если отчёт без PIN - сразу успех
    if not report.pin_hash:
        return PinVerifyResponse(success=True, message="No PIN required")
    
    # Проверяем PIN
    service = ReportService(db)
    if service.verify_pin(pin_data.pin, report.pin_hash):
        # Успешная проверка - создаём сессию
        await report_pin_service.reset_attempts(code, client_ip)
        
        try:
            redis = await get_redis()
            if redis:
                session_key = f"report_pin_session:{code}:{client_ip}"
                # Сессия на 1 час
                await redis.setex(session_key, 3600, "1")
        except Exception as e:
            logger.warning(f"Redis error creating PIN session: {e}")
        
        logger.info(f"PIN verified for report {code} from {client_ip}")
        
        return PinVerifyResponse(success=True, message="PIN verified")
    
    # Неверный PIN
    attempts_left = await report_pin_service.increment_attempts(code, client_ip)
    
    logger.warning(f"Invalid PIN attempt for report {code} from {client_ip}, {attempts_left} attempts left")
    
    if attempts_left == 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts",
            headers={"Retry-After": str(PIN_LOCKOUT_SECONDS)}
        )
    
    return PinVerifyResponse(
        success=False,
        message="Invalid PIN",
        attempts_left=attempts_left
    )


@router.get("/report/{code}/student/{student_id}", response_model=StudentDetailData)
@limiter.limit("100/minute")
async def get_public_student_report(
    request: Request,
    code: str,
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Получить детальные данные студента из публичного отчёта.
    
    - **code**: 8-символьный код отчёта
    - **student_id**: UUID студента
    
    Если отчёт защищён PIN-кодом, требуется предварительная верификация.
    """
    report = await _get_valid_report(db, code, request=request)
    client_ip = _get_client_ip(request)
    
    # Проверка PIN-защиты
    if report.pin_hash:
        try:
            redis = await get_redis()
            if redis:
                session_key = f"report_pin_session:{code}:{client_ip}"
                session_valid = await redis.get(session_key)
                
                if not session_valid:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="PIN required",
                        headers={"X-Has-Pin": "true"}
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="PIN required",
                    headers={"X-Has-Pin": "true"}
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Redis error checking PIN session for student: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="PIN required",
                headers={"X-Has-Pin": "true"}
            )
    
    # Собираем данные студента
    service = ReportService(db)
    student_data = await service.get_student_report_data(report, student_id)
    
    if not student_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found in this report"
        )
    
    # Логируем просмотр
    user_agent = request.headers.get("User-Agent")
    await service.log_view(report.id, client_ip, user_agent)
    
    logger.info(f"Student {student_id} report viewed from {client_ip} via report {code}")
    
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
            "message": "Report not found"
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
        "message": "Report expired" if is_expired else ("Report not available" if not report.is_active else "OK")
    }
