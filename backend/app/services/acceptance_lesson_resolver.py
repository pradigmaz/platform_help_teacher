"""Shared lesson resolution helpers for legacy submission acceptance flows."""

from datetime import date
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lesson, User
from app.models.schedule import LessonType
from app.services.schedule_constants import today_msk

_ACCEPTANCE_LESSON_TYPES = (LessonType.LAB, LessonType.PRACTICE)


def _matches_student_subgroup(lesson: Lesson, student_subgroup: int | None) -> bool:
    if student_subgroup is None:
        return lesson.subgroup is None
    return lesson.subgroup in (None, student_subgroup)


def _matches_student_lesson_scope(lesson: Lesson, *, student: User, subject_id: UUID) -> bool:
    if lesson.subject_id != subject_id or lesson.group_id != student.group_id:
        return False
    if lesson.lesson_type not in _ACCEPTANCE_LESSON_TYPES:
        return False
    if lesson.is_cancelled:
        return False
    return _matches_student_subgroup(lesson, student.subgroup)


def _pick_best_lesson(lessons: list[Lesson], student_subgroup: int | None) -> Lesson | None:
    compatible = [lesson for lesson in lessons if _matches_student_subgroup(lesson, student_subgroup)]
    if not compatible:
        return None
    return min(
        compatible,
        key=lambda lesson: (
            0 if lesson.subgroup == student_subgroup else 1,
            str(getattr(lesson, "id", "")),
        ),
    )


def _build_student_lesson_conditions(student: User, subject_id: UUID):
    conditions = [
        Lesson.subject_id == subject_id,
        Lesson.group_id == student.group_id,
        Lesson.lesson_type.in_(_ACCEPTANCE_LESSON_TYPES),
        Lesson.is_cancelled.is_(False),
    ]
    if student.subgroup is None:
        conditions.append(Lesson.subgroup.is_(None))
    else:
        conditions.append(or_(Lesson.subgroup == student.subgroup, Lesson.subgroup.is_(None)))
    return conditions


async def resolve_lesson_from_submission_context(
    db: AsyncSession,
    *,
    student: User,
    subject_id: UUID,
    lesson_id: UUID | None,
    lesson_date: date | None,
    lesson_number: int | None,
) -> Lesson | None:
    """Resolve a lesson captured on the submission itself, if still valid."""
    if student.group_id is None:
        return None

    if lesson_id is not None:
        lesson = await db.get(Lesson, lesson_id)
        if lesson is not None and _matches_student_lesson_scope(lesson, student=student, subject_id=subject_id):
            return lesson

    if lesson_date is None or lesson_number is None:
        return None

    conditions = _build_student_lesson_conditions(student, subject_id)
    conditions.extend([Lesson.date == lesson_date, Lesson.lesson_number == lesson_number])

    result = await db.execute(select(Lesson).where(and_(*conditions)))
    return _pick_best_lesson(list(result.scalars().all()), student.subgroup)


async def find_latest_lesson_for_student(
    db: AsyncSession,
    *,
    student: User,
    subject_id: UUID,
    on_or_before: date | None = None,
) -> Lesson | None:
    """Resolve the latest suitable lesson for a student's acceptance/journal context."""
    if student.group_id is None:
        return None

    target_date = on_or_before or today_msk()
    conditions = _build_student_lesson_conditions(student, subject_id)
    conditions.append(Lesson.date <= target_date)

    result = await db.execute(
        select(Lesson).where(and_(*conditions)).order_by(Lesson.date.desc(), Lesson.lesson_number.desc())
    )
    lessons = list(result.scalars().all())
    if not lessons:
        return None

    latest_date = lessons[0].date
    latest_number = lessons[0].lesson_number
    latest_slot_candidates = [
        lesson for lesson in lessons if lesson.date == latest_date and lesson.lesson_number == latest_number
    ]
    return _pick_best_lesson(latest_slot_candidates, student.subgroup)
