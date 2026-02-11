"""
Валидатор слотов для сдачи лабораторных работ.
Правило: 1 пара = 1 лаба, но EXCUSED-студенты получают +1 слот.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import Attendance, AttendanceStatus
from app.models.lab import Lab
from app.models.lesson import Lesson
from app.models.lesson_grade import LessonGrade
from app.models.schedule import LessonType

logger = logging.getLogger(__name__)


async def get_excused_lab_ids(db: AsyncSession, student_id: UUID, subject_id: UUID) -> set[UUID]:
    """
    Получить ID лаб, созданных на занятиях где студент был EXCUSED.
    Эти лабы не имеют дедлайна для данного студента.
    """
    # Находим LAB-занятия где студент EXCUSED
    excused_lessons_query = (
        select(Lesson.id)
        .join(
            Attendance,
            and_(
                Attendance.lesson_id == Lesson.id,
                Attendance.student_id == student_id,
                Attendance.status == AttendanceStatus.EXCUSED,
            ),
        )
        .where(
            and_(Lesson.subject_id == subject_id, Lesson.lesson_type == LessonType.LAB, Lesson.is_cancelled.is_(False))
        )
    )
    result = await db.execute(excused_lessons_query)
    excused_lesson_ids = {row[0] for row in result.fetchall()}

    if not excused_lesson_ids:
        return set()

    # Находим лабы, привязанные к этим занятиям
    labs_query = select(Lab.id).where(and_(Lab.lesson_id.in_(excused_lesson_ids), Lab.deleted_at.is_(None)))
    result = await db.execute(labs_query)
    return {row[0] for row in result.fetchall()}


async def get_unsubmitted_excused_labs_count(db: AsyncSession, student_id: UUID, subject_id: UUID) -> int:
    """
    Количество несданных EXCUSED-лаб.
    Если > 0, студент получает бонусный слот (+1 лаба за пару).
    """
    excused_lab_ids = await get_excused_lab_ids(db, student_id, subject_id)
    if not excused_lab_ids:
        return 0

    # Считаем сколько из них уже сдано (есть оценка)
    # Нужно найти лабы по номеру, т.к. оценки хранятся по work_number
    labs_query = select(Lab.number).where(Lab.id.in_(excused_lab_ids))
    result = await db.execute(labs_query)
    excused_lab_numbers = {row[0] for row in result.fetchall()}

    if not excused_lab_numbers:
        return 0

    # Считаем оценки студента по этим номерам лаб
    grades_query = (
        select(func.count(func.distinct(LessonGrade.work_number)))
        .join(Lesson, LessonGrade.lesson_id == Lesson.id)
        .where(
            and_(
                LessonGrade.student_id == student_id,
                Lesson.subject_id == subject_id,
                LessonGrade.work_number.in_(excused_lab_numbers),
                LessonGrade.grade.isnot(None),
            )
        )
    )
    result = await db.execute(grades_query)
    submitted_count = result.scalar() or 0

    return len(excused_lab_numbers) - submitted_count


async def get_grades_count_on_lesson(
    db: AsyncSession, student_id: UUID, lesson_id: UUID, exclude_work_number: int | None = None
) -> int:
    """
    Количество оценок за лабы у студента на данном занятии.

    Args:
        exclude_work_number: Исключить эту работу из подсчёта (для upsert)
    """
    conditions = [
        LessonGrade.lesson_id == lesson_id,
        LessonGrade.student_id == student_id,
        LessonGrade.grade.isnot(None),
    ]
    if exclude_work_number is not None:
        conditions.append(LessonGrade.work_number != exclude_work_number)

    query = select(func.count()).select_from(LessonGrade).where(and_(*conditions))
    result = await db.execute(query)
    return result.scalar() or 0


async def get_max_labs_per_lesson(
    db: AsyncSession, student_id: UUID, subject_id: UUID, lesson: Optional["Lesson"] = None
) -> int:
    """
    Максимум лаб, которые студент может сдать за одно занятие.
    1 — обычно, 2 — если есть несданные EXCUSED-лабы.

    Args:
        lesson: Если передан и имеет max_labs_override, используется это значение
    """
    if lesson is not None and lesson.max_labs_override is not None:
        logger.info(
            f"[lab_slot_validator:get_max_labs_per_lesson] Using max_labs_override={lesson.max_labs_override} "
            f"for lesson_id={lesson.id}, student_id={student_id}"
        )
        return lesson.max_labs_override

    unsubmitted = await get_unsubmitted_excused_labs_count(db, student_id, subject_id)
    result = 2 if unsubmitted > 0 else 1
    logger.info(
        f"[lab_slot_validator:get_max_labs_per_lesson] student_id={student_id}, "
        f"unsubmitted_excused={unsubmitted}, max_labs={result}"
    )
    return result


async def validate_lab_submission(
    db: AsyncSession,
    student_id: UUID,
    lesson_id: UUID,
    subject_id: UUID,
    work_number: int | None = None,
    lesson: Optional["Lesson"] = None,
) -> None:
    """
    Проверить, может ли студент сдать ещё одну лабу на этом занятии.

    Args:
        work_number: Номер работы (для upsert — исключить из подсчёта)
        lesson: Объект занятия (для учёта max_labs_override)

    Raises:
        ValueError: Если лимит исчерпан
    """
    # Проверяем, существует ли уже оценка для этой работы (upsert)
    if work_number is not None:
        existing = await db.execute(
            select(LessonGrade).where(
                and_(
                    LessonGrade.lesson_id == lesson_id,
                    LessonGrade.student_id == student_id,
                    LessonGrade.work_number == work_number,
                )
            )
        )
        if existing.scalar_one_or_none() is not None:
            return  # Обновление существующей оценки — слоты не проверяем

    current_count = await get_grades_count_on_lesson(db, student_id, lesson_id)
    max_allowed = await get_max_labs_per_lesson(db, student_id, subject_id, lesson)

    if current_count >= max_allowed:
        if max_allowed == 1:
            raise ValueError("Лимит: 1 лабораторная за занятие")
        else:
            raise ValueError(f"Лимит: {max_allowed} лабораторных за занятие (бонус за пропуски)")


async def is_excused_lab(db: AsyncSession, student_id: UUID, lab: Lab) -> bool:
    """
    Проверить, является ли лаба EXCUSED для студента.
    (Студент был EXCUSED на занятии, где лаба была создана)
    """
    if not lab.lesson_id:
        return False

    query = select(Attendance).where(
        and_(
            Attendance.lesson_id == lab.lesson_id,
            Attendance.student_id == student_id,
            Attendance.status == AttendanceStatus.EXCUSED,
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None
