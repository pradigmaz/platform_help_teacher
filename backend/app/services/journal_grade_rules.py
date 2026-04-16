"""Shared validation rules for journal grade writes."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lesson, User
from app.models.schedule import LessonType
from app.services.attestation.deadline_validator import get_max_allowed_grade, validate_grade_for_max

WORK_NUMBER_REQUIRED_TYPES = {LessonType.LAB, LessonType.PRACTICE}
SUBMISSION_SYNC_TYPES = {LessonType.LAB, LessonType.PRACTICE}


class JournalGradeRuleError(ValueError):
    """Domain validation error for grade write rules."""


def resolve_work_number(lesson: Lesson, work_number: int | None) -> int | None:
    if lesson.lesson_type not in WORK_NUMBER_REQUIRED_TYPES:
        return work_number

    resolved_work_number = work_number if work_number is not None else lesson.work_number
    if resolved_work_number is None:
        raise JournalGradeRuleError("Для lab/practice номер работы обязателен")
    return resolved_work_number


def validate_lesson_write(lesson: Lesson) -> None:
    if lesson.is_cancelled:
        raise JournalGradeRuleError("Нельзя выставлять оценки в отменённом занятии")


async def validate_student_membership(db: AsyncSession, lesson: Lesson, student_id: UUID) -> None:
    student = await db.get(User, student_id)
    if not student:
        raise JournalGradeRuleError("Студент не найден")
    if student.group_id != lesson.group_id:
        raise JournalGradeRuleError(f"Student {student_id} not in group {lesson.group_id}")
    if lesson.subgroup is not None and student.subgroup != lesson.subgroup:
        raise JournalGradeRuleError(f"Student {student_id} not in subgroup {lesson.subgroup}")


async def validate_grade_limits(
    db: AsyncSession,
    lesson: Lesson,
    student_id: UUID,
    work_number: int | None,
    grade: int,
) -> None:
    max_allowed = await get_max_allowed_grade(db, lesson, student_id=student_id, work_number=work_number)
    validate_grade_for_max(grade, max_allowed)
