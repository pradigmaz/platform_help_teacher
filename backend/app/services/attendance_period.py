"""Shared period-aware lesson and attendance loading helpers."""

from collections import defaultdict
from collections.abc import Iterable
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import Attendance
from app.models.lesson import Lesson
from app.services.attendance_slots import build_attendance_slot_filter, get_lesson_slot_sets, matches_attendance_slot


async def load_period_lessons(
    db: AsyncSession,
    *,
    group_id: UUID,
    period_start: date,
    period_end: date,
    subject_id: UUID | None = None,
) -> list[Lesson]:
    """Load non-cancelled lessons for the requested period."""

    query = (
        select(Lesson)
        .where(Lesson.group_id == group_id)
        .where(Lesson.is_cancelled.is_(False))
        .where(Lesson.date >= period_start)
        .where(Lesson.date <= period_end)
        .order_by(Lesson.date.asc(), Lesson.lesson_number.asc())
    )
    if subject_id is not None:
        query = query.where(Lesson.subject_id == subject_id)

    result = await db.execute(query)
    return list(result.scalars().all())


def group_lessons_by_subgroup(lessons: Iterable[Lesson]) -> dict[int | None, list[Lesson]]:
    """Group lessons by subgroup while preserving lesson order."""

    grouped: dict[int | None, list[Lesson]] = defaultdict(list)
    for lesson in lessons:
        grouped[lesson.subgroup].append(lesson)
    return grouped


def get_relevant_lessons_for_subgroup(
    lessons_by_subgroup: dict[int | None, list[Lesson]],
    subgroup: int | None,
) -> list[Lesson]:
    """Return lessons relevant for a student subgroup."""

    if subgroup is None:
        return list(lessons_by_subgroup.get(None, []))
    return list(lessons_by_subgroup.get(None, [])) + list(lessons_by_subgroup.get(subgroup, []))


def calculate_expected_lessons(relevant_lessons: Iterable[Lesson], *, minimum: int = 0) -> int:
    """Return expected lesson count with an optional lower bound."""

    return max(len(list(relevant_lessons)), minimum)


async def load_attendance_by_student_for_lessons(
    db: AsyncSession,
    *,
    group_id: UUID,
    student_ids: list[UUID],
    lessons: list[Lesson],
) -> dict[UUID, list[Attendance]]:
    """Load attendance rows for the provided lesson slots and group them by student."""

    if not lessons or not student_ids:
        return {}

    slot_filter = build_attendance_slot_filter(lessons)
    query = select(Attendance).where(
        Attendance.group_id == group_id,
        Attendance.student_id.in_(student_ids),
        slot_filter,
    )
    result = await db.execute(query)

    grouped: dict[UUID, list[Attendance]] = defaultdict(list)
    for record in result.scalars().all():
        grouped[record.student_id].append(record)
    return grouped


def filter_attendance_records_to_lessons(
    attendance_records: Iterable[Attendance], lessons: list[Lesson]
) -> list[Attendance]:
    """Filter attendance records down to the exact lesson slots for one student."""

    lesson_ids, legacy_slots = get_lesson_slot_sets(lessons)
    return [
        record
        for record in attendance_records
        if matches_attendance_slot(record, lesson_ids=lesson_ids, legacy_slots=legacy_slots)
    ]
