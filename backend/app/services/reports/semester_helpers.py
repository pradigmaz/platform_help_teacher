"""
Хелперы для работы с семестром и аттестацией.
"""
from datetime import date, timedelta
from typing import Tuple, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attestation_settings import AttestationType, AttestationSettings
from app.services.attestation.settings import AttestationSettingsManager


EARLY_SEMESTER_WEEKS = 6  # Первые 6 недель - "начало семестра"


async def get_semester_start_date(db: AsyncSession) -> Optional[date]:
    """Получить дату начала семестра из настроек FIRST аттестации."""
    settings_manager = AttestationSettingsManager(db)
    settings = await settings_manager.get_settings(AttestationType.FIRST)
    return settings.semester_start_date if settings else None


async def get_current_semester_from_settings(db: AsyncSession) -> Tuple[int, int]:
    """
    Определить текущий семестр на основе semester_start_date.
    
    Если semester_start_date задан:
    - Если месяц начала >= 9 (сентябрь) → 1 семестр
    - Если месяц начала <= 5 (май) → 2 семестр
    
    Fallback на хардкод если настройки не заданы.
    """
    semester_start = await get_semester_start_date(db)
    
    if semester_start:
        if semester_start.month >= 9:
            return (semester_start.year, 1)
        elif semester_start.month <= 5:
            return (semester_start.year - 1, 2)
        else:
            return (semester_start.year - 1, 2)
    
    # Fallback на текущую дату
    now = date.today()
    if now.month >= 9:
        return (now.year, 1)
    elif now.month <= 5:
        return (now.year - 1, 2)
    else:
        return (now.year - 1, 2)


async def get_semester_info(
    db: AsyncSession, 
    attestation_type: AttestationType
) -> Tuple[bool, int, int, bool]:
    """Получить информацию о семестре.
    
    Returns:
        Tuple[is_early, max_points, min_passing_points, is_second_available]
    """
    settings_manager = AttestationSettingsManager(db)
    settings = await settings_manager.get_settings(AttestationType.FIRST)
    
    max_points = attestation_type.max_points
    min_passing = AttestationSettings.get_min_passing_points(attestation_type)
    
    if not settings or not settings.semester_start_date:
        return True, max_points, min_passing, False
    
    today = date.today()
    early_end = settings.semester_start_date + timedelta(weeks=EARLY_SEMESTER_WEEKS)
    is_early = today < early_end
    
    second_available_date = settings.semester_start_date + timedelta(weeks=8)
    is_second_available = today >= second_available_date
    
    return is_early, max_points, min_passing, is_second_available
