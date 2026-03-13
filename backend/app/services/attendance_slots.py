"""Helpers for matching attendance records to concrete lesson slots."""

from collections.abc import Iterable
from datetime import date
from uuid import UUID

from sqlalchemy import and_, false, or_, tuple_

from app.models import Attendance, Lesson

LessonSlot = tuple[date, int | None]


def get_lesson_slot_sets(lessons: Iterable[Lesson]) -> tuple[set[UUID], set[LessonSlot]]:
    """Build lesson-id and legacy (date, lesson_number) slot sets."""
    lesson_ids: set[UUID] = set()
    legacy_slots: set[LessonSlot] = set()

    for lesson in lessons:
        lesson_ids.add(lesson.id)
        legacy_slots.add((lesson.date, lesson.lesson_number))

    return lesson_ids, legacy_slots


def build_attendance_slot_filter(lessons: Iterable[Lesson]):
    """Return a SQLAlchemy filter matching attendance for the provided lessons."""
    lesson_ids, legacy_slots = get_lesson_slot_sets(lessons)
    filters = []

    if lesson_ids:
        filters.append(Attendance.lesson_id.in_(list(lesson_ids)))
    if legacy_slots:
        filters.append(
            and_(
                Attendance.lesson_id.is_(None),
                tuple_(Attendance.date, Attendance.lesson_number).in_(list(legacy_slots)),
            )
        )

    if not filters:
        return false()
    if len(filters) == 1:
        return filters[0]
    return or_(*filters)


def matches_attendance_slot(
    attendance: Attendance,
    *,
    lesson_ids: set[UUID],
    legacy_slots: set[LessonSlot],
) -> bool:
    """Check whether an attendance row belongs to one of the lesson slots."""
    if attendance.lesson_id is not None:
        return attendance.lesson_id in lesson_ids
    return (attendance.date, attendance.lesson_number) in legacy_slots
