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
from app.models.lesson import Lesson
from app.models.schedule import LessonType
from app.services.deadline_context import build_deadline_context_for_current_lesson
from app.services.deadline_engine import evaluate_deadline_context
from app.services.deadline_inputs import load_active_extension_bonus
from app.services.deadline_lesson_loader import load_ordered_deadline_lessons, load_origin_lessons
from app.services.deadline_trace import DeadlineTrace, resolve_effective_deadline_date
from app.services.lab_lookup import find_active_lab_by_subject_and_number

logger = logging.getLogger(__name__)
_DEADLINE_LESSON_TYPES = (LessonType.LAB, LessonType.PRACTICE)


async def _get_origin_lesson_for_group(
    db: AsyncSession,
    current_lesson: Lesson,
    lab_number: int,
) -> Lesson | None:
    """Resolve the first lesson slot for this lab in the current lesson's group."""
    return (
        await load_origin_lessons(
            db,
            group_id=current_lesson.group_id,
            subject_id=current_lesson.subject_id,
            work_numbers={lab_number},
        )
    ).get(lab_number)


async def _get_lesson_positions(
    db: AsyncSession,
    origin_lesson: Lesson,
) -> dict[UUID, int]:
    """Build lesson position map for deadline evaluation from the origin lesson onward."""
    ordered_lessons = await load_ordered_deadline_lessons(
        db,
        group_id=origin_lesson.group_id,
        subject_id=origin_lesson.subject_id,
        since_date=origin_lesson.date,
    )
    return {lesson_id: idx for idx, (lesson_id, _, _, _) in enumerate(ordered_lessons)}


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
    trace = await get_deadline_trace_for_lab(db, lab, current_lesson, student_id)
    return trace.current_max_grade if trace else 5


async def get_deadline_trace_for_lab(
    db: AsyncSession,
    lab: Lab,
    current_lesson: Lesson,
    student_id: UUID | None = None,
) -> DeadlineTrace | None:
    """Get traceable deadline state for a lab on a concrete lesson."""
    origin_lesson = await _get_origin_lesson_for_group(db, current_lesson, lab.number)
    if not origin_lesson:
        return None

    # Если нет дедлайнов — нет содержательного trace для teacher acceptance path.
    if lab.deadline_5_lessons is None and lab.deadline_4_lessons is None:
        return None

    is_excused_origin = False
    if student_id:
        excused_query = select(Attendance).where(
            and_(
                Attendance.lesson_id == origin_lesson.id,
                Attendance.student_id == student_id,
                Attendance.status == AttendanceStatus.EXCUSED,
            )
        )
        excused_result = await db.execute(excused_query)
        is_excused_origin = excused_result.scalar_one_or_none() is not None

    bonus_lessons = await load_active_extension_bonus(
        db,
        lab_id=lab.id,
        group_id=current_lesson.group_id,
        now=datetime.now(UTC),
    )
    ordered_lessons = await load_ordered_deadline_lessons(
        db,
        group_id=origin_lesson.group_id,
        subject_id=origin_lesson.subject_id,
        since_date=origin_lesson.date,
    )
    lesson_positions = await _get_lesson_positions(db, origin_lesson)
    context = build_deadline_context_for_current_lesson(
        lab_number=lab.number,
        origin_lesson_id=origin_lesson.id,
        current_lesson_id=current_lesson.id,
        lesson_positions=lesson_positions,
        extension_bonus=bonus_lessons,
        is_excused_origin=is_excused_origin,
    )
    if context.lesson_index is None:
        return None

    ordered_lessons_for_trace = [(work_number, lesson_date) for _, work_number, lesson_date, _ in ordered_lessons]
    effective_deadline_5_date = resolve_effective_deadline_date(
        ordered_lessons=ordered_lessons_for_trace,
        lab_number=lab.number,
        effective_deadline_lessons=bonus_lessons + lab.deadline_5_lessons
        if lab.deadline_5_lessons is not None
        else None,
    )
    effective_deadline_4_date = resolve_effective_deadline_date(
        ordered_lessons=ordered_lessons_for_trace,
        lab_number=lab.number,
        effective_deadline_lessons=bonus_lessons + lab.deadline_4_lessons
        if lab.deadline_4_lessons is not None
        else None,
    )
    evaluation = evaluate_deadline_context(
        context=context,
        deadline_5_lessons=lab.deadline_5_lessons,
        deadline_4_lessons=lab.deadline_4_lessons,
        effective_deadline_5_date=effective_deadline_5_date,
        effective_deadline_4_date=effective_deadline_4_date,
    )
    return evaluation.trace


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
    if lesson.lesson_type not in _DEADLINE_LESSON_TYPES:
        return 5

    lab_number = work_number or lesson.work_number
    if not lab_number:
        return 5

    if lesson.subject_id is None:
        return 5

    lab = await find_active_lab_by_subject_and_number(db, lesson.subject_id, lab_number)

    if not lab:
        return 5

    return await get_max_allowed_grade_for_lab(db, lab, lesson, student_id)
