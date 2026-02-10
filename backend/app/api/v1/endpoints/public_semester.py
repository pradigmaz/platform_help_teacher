"""
Public API endpoint для информации о семестре.

Без авторизации. Rate limiting для защиты.
"""

import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.limiter import limiter
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/semester-info")
@limiter.limit("100/minute")
async def get_semester_info(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Получить информацию о текущем семестре.

    Публичный эндпоинт для фронтенда.
    Возвращает semester_start_date и вычисленный семестр.
    """
    from app.services.reports.semester_helpers import (
        get_current_semester_from_settings,
        get_semester_start_date,
    )

    semester_start = await get_semester_start_date(db)
    academic_year, semester = await get_current_semester_from_settings(db)

    return {
        "semester_start_date": semester_start.isoformat() if semester_start else None,
        "academic_year": academic_year,
        "semester": semester,
    }
