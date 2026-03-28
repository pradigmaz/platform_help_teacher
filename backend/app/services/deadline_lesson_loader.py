"""Shared lesson-sequence loaders for legacy deadline and visibility paths."""

from datetime import date
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson import Lesson
from app.models.schedule import LessonType

_DEADLINE_LESSON_TYPES = (LessonType.LAB, LessonType.PRACTICE)


def build_deadline_lesson_filter(
    *,
    group_id: UUID,
    subject_id: UUID | None,
    subgroup: int | None = None,
    since_date: date | None = None,
    until_date: date | None = None,
) -> list:
    conditions = [
        Lesson.group_id == group_id,
        Lesson.lesson_type.in_(_DEADLINE_LESSON_TYPES),
        Lesson.is_cancelled.is_(False),
    ]
    if subject_id is not None:
        conditions.append(Lesson.subject_id == subject_id)
    if subgroup is not None:
        conditions.append((Lesson.subgroup.is_(None)) | (Lesson.subgroup == subgroup))
    if since_date is not None:
        conditions.append(Lesson.date >= since_date)
    if until_date is not None:
        conditions.append(Lesson.date <= until_date)
    return conditions


async def load_origin_lessons(
    db: AsyncSession,
    *,
    group_id: UUID | None,
    subject_id: UUID | None,
    work_numbers: set[int],
    subgroup: int | None = None,
) -> dict[int, Lesson]:
    if group_id is None or subject_id is None or not work_numbers:
        return {}

    result = await db.execute(
        select(Lesson)
        .where(
            and_(
                *build_deadline_lesson_filter(
                    group_id=group_id,
                    subject_id=subject_id,
                    subgroup=subgroup,
                ),
                Lesson.work_number.in_(work_numbers),
            )
        )
        .order_by(Lesson.work_number, Lesson.date, Lesson.lesson_number)
    )

    origins: dict[int, Lesson] = {}
    for lesson in result.scalars().all():
        if lesson.work_number is None or lesson.work_number in origins:
            continue
        origins[lesson.work_number] = lesson
    return origins


async def load_ordered_deadline_lessons(
    db: AsyncSession,
    *,
    group_id: UUID | None,
    subject_id: UUID | None,
    subgroup: int | None = None,
    since_date: date | None = None,
    until_date: date | None = None,
) -> list[tuple[UUID, int | None, date, int]]:
    if group_id is None or subject_id is None:
        return []

    result = await db.execute(
        select(Lesson.id, Lesson.work_number, Lesson.date, Lesson.lesson_number)
        .where(
            and_(
                *build_deadline_lesson_filter(
                    group_id=group_id,
                    subject_id=subject_id,
                    subgroup=subgroup,
                    since_date=since_date,
                    until_date=until_date,
                )
            )
        )
        .order_by(Lesson.date, Lesson.lesson_number)
    )
    return [
        (lesson_id, work_number, lesson_date, lesson_number)
        for lesson_id, work_number, lesson_date, lesson_number in result.all()
    ]
