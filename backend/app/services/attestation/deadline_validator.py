"""
Валидатор дедлайнов для оценок.
Проверяет максимально допустимую оценку с учётом просрочки.
"""
import logging
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.lesson import Lesson
from app.models.work import Work

logger = logging.getLogger(__name__)


async def get_max_allowed_grade(
    db: AsyncSession,
    lesson: Lesson,
    submission_date: Optional[date] = None,
    has_excuse: bool = False
) -> int:
    """
    Получить максимально допустимую оценку с учётом дедлайна.
    
    Args:
        db: Сессия БД
        lesson: Занятие, на котором ставится оценка
        submission_date: Дата сдачи (по умолчанию = дата занятия)
        has_excuse: Есть ли уважительная причина (снимает ограничение)
    
    Returns:
        Максимально допустимая оценка (2-5)
    """
    # Уважительная причина снимает ограничение
    if has_excuse:
        return 5
    
    # Если нет связанной работы — нет дедлайна
    if not lesson.work_id:
        return 5
    
    # Получаем работу
    work_result = await db.execute(select(Work).where(Work.id == lesson.work_id))
    work = work_result.scalar_one_or_none()
    
    if not work or not work.deadline:
        return 5
    
    # Дата сдачи = дата занятия если не указана
    check_date = submission_date or lesson.date
    
    # Приводим к date для сравнения
    deadline_date = work.deadline.date() if isinstance(work.deadline, datetime) else work.deadline
    
    if check_date <= deadline_date:
        return 5  # Вовремя
    
    # Получаем настройки аттестации
    settings = await _get_attestation_settings(db, lesson.date)
    if not settings:
        return 5  # Нет настроек — нет ограничений
    
    days_late = (check_date - deadline_date).days
    
    if days_late <= settings.late_threshold_days:
        return settings.late_max_grade  # Немного просрочил → макс 4
    
    return settings.very_late_max_grade  # Сильно просрочил → макс 3


async def _get_attestation_settings(
    db: AsyncSession,
    lesson_date: date
) -> Optional[AttestationSettings]:
    """Получить настройки аттестации для даты занятия."""
    # Определяем тип аттестации по дате (упрощённо — берём первую)
    # TODO: Улучшить логику определения периода
    result = await db.execute(
        select(AttestationSettings)
        .where(AttestationSettings.attestation_type == AttestationType.FIRST)
    )
    return result.scalar_one_or_none()


def validate_grade_for_max(grade: int, max_allowed: int) -> None:
    """
    Проверить, что оценка не превышает максимум.
    
    Raises:
        ValueError: Если оценка превышает максимум
    """
    if grade > max_allowed:
        raise ValueError(
            f"Максимальная оценка для этой работы: {max_allowed} (просрочка дедлайна)"
        )
