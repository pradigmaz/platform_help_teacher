"""
Валидатор дедлайнов для оценок лабораторных.
Проверяет максимально допустимую оценку с учётом количества прошедших пар.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import Attendance, AttendanceStatus
from app.models.lab import Lab
from app.models.lab_deadline_extension import LabDeadlineExtension
from app.models.lesson import Lesson
from app.models.schedule import LessonType

logger = logging.getLogger(__name__)


async def get_max_allowed_grade_for_lab(
    db: AsyncSession, lab: Lab, current_lesson: Lesson, student_id: UUID | None = None
) -> int:
    """
    Получить максимально допустимую оценку для лабораторной с учётом дедлайна.

    Args:
        db: Сессия БД
        lab: Лабораторная работа
        current_lesson: Занятие на котором ставится оценка
        student_id: ID студента (для проверки EXCUSED на origin_lesson)

    Returns:
        Максимально допустимая оценка (2-5)
    """
    # Если лаба не привязана к занятию — нет ограничений
    if not lab.lesson_id:
        return 5

    # Проверяем EXCUSED на занятии создания лабы (origin_lesson)
    # Если студент был EXCUSED когда лаба создана — дедлайн не применяется
    if student_id:
        excused_query = select(Attendance).where(
            and_(
                Attendance.lesson_id == lab.lesson_id,
                Attendance.student_id == student_id,
                Attendance.status == AttendanceStatus.EXCUSED,
            )
        )
        excused_result = await db.execute(excused_query)
        if excused_result.scalar_one_or_none() is not None:
            return 5  # EXCUSED-лаба — без дедлайна

    # Если нет дедлайнов — нет ограничений
    if lab.deadline_5_lessons is None and lab.deadline_4_lessons is None:
        return 5

    # Получаем занятие на котором создана лаба
    origin_lesson = await db.get(Lesson, lab.lesson_id)
    if not origin_lesson:
        return 5

    # Проверяем продление дедлайна для группы студента
    bonus_lessons = await _get_extension_bonus(db, lab.id, current_lesson.group_id)

    # Считаем номер текущей пары относительно создания лабы
    lesson_index = await _get_lesson_index(db, origin_lesson=origin_lesson, current_lesson=current_lesson)

    if lesson_index is None:
        return 5

    # Применяем бонус от продления
    effective_deadline_5 = (lab.deadline_5_lessons or 0) + bonus_lessons if lab.deadline_5_lessons is not None else None
    effective_deadline_4 = (lab.deadline_4_lessons or 0) + bonus_lessons if lab.deadline_4_lessons is not None else None

    # Проверяем дедлайны
    # lesson_index = 0 — это пара создания лабы
    # deadline_5_lessons = 1 — можно сдать на 5 на паре 0 и 1 (текущая + следующая)

    if effective_deadline_4 is not None and lesson_index > effective_deadline_4:
        return 3  # Сильно просрочил → макс 3

    if effective_deadline_5 is not None and lesson_index > effective_deadline_5:
        return 4  # Немного просрочил → макс 4

    return 5  # Вовремя


async def _get_extension_bonus(db: AsyncSession, lab_id: UUID, group_id: UUID | None) -> int:
    """Получить бонус пар от продления дедлайна для группы."""
    if not group_id:
        return 0

    now = datetime.now(UTC)

    query = select(LabDeadlineExtension.bonus_lessons).where(
        and_(
            LabDeadlineExtension.lab_id == lab_id,
            LabDeadlineExtension.group_id == group_id,
            LabDeadlineExtension.is_active,
            # Не истекло (expires_at is NULL или > now)
            (LabDeadlineExtension.expires_at.is_(None)) | (LabDeadlineExtension.expires_at > now),
        )
    )

    result = await db.execute(query)
    bonus = result.scalar_one_or_none()

    return bonus or 0


async def _get_lesson_index(db: AsyncSession, origin_lesson: Lesson, current_lesson: Lesson) -> int | None:
    """
    Получить индекс текущего занятия относительно занятия создания лабы.
    Считаются только LAB-занятия той же группы и предмета.

    Returns:
        Индекс (0 = пара создания), None если не найдено
    """
    query = (
        select(Lesson.id, Lesson.date, Lesson.lesson_number)
        .where(
            and_(
                Lesson.group_id == origin_lesson.group_id,
                Lesson.subject_id == origin_lesson.subject_id,
                Lesson.lesson_type == LessonType.LAB,
                Lesson.is_cancelled.is_(False),
                Lesson.date >= origin_lesson.date,
            )
        )
        .order_by(Lesson.date, Lesson.lesson_number)
    )

    result = await db.execute(query)
    lessons = result.all()

    for idx, (lesson_id, _, _) in enumerate(lessons):
        if lesson_id == current_lesson.id:
            return idx

    return None


def validate_grade_for_max(grade: int, max_allowed: int) -> None:
    """
    Проверить, что оценка не превышает максимум.

    Raises:
        ValueError: Если оценка превышает максимум
    """
    if grade > max_allowed:
        raise ValueError(f"Максимальная оценка для этой работы: {max_allowed} (просрочка дедлайна)")


async def get_max_allowed_grade(
    db: AsyncSession, lesson: Lesson, student_id: UUID | None = None, work_number: int | None = None
) -> int:
    """
    Получить максимально допустимую оценку для занятия.

    Args:
        db: Сессия БД
        lesson: Занятие на котором ставится оценка
        student_id: ID студента (для проверки EXCUSED на origin_lesson)
        work_number: Номер работы (если отличается от lesson.work_number)

    Returns:
        Максимально допустимая оценка (2-5)
    """
    if lesson.lesson_type != LessonType.LAB:
        return 5

    lab_number = work_number or lesson.work_number
    if not lab_number:
        return 5

    lab_query = select(Lab).where(
        and_(Lab.subject_id == lesson.subject_id, Lab.number == lab_number, Lab.deleted_at.is_(None))
    )
    result = await db.execute(lab_query)
    lab = result.scalar_one_or_none()

    if not lab:
        return 5

    return await get_max_allowed_grade_for_lab(db, lab, lesson, student_id)
