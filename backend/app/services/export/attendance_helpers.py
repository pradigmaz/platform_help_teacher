"""Shared helpers for export lessons and attendance rows."""

from __future__ import annotations

import logging
from datetime import date
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson import Lesson
from app.models.user import User
from app.schemas.export import AttendanceExportRow, LessonExportColumn
from app.services.attendance_contract import build_student_attendance_snapshots, snapshot_to_report_stats
from app.services.attendance_period import load_attendance_by_student_for_lessons

logger = logging.getLogger(__name__)


def filter_students_for_subgroup(students: list[User], subgroup: int | None) -> list[User]:
    """Keep only students from the selected subgroup."""
    if subgroup is None:
        return students

    return [student for student in students if student.subgroup == subgroup]


def filter_students_for_export(
    students: list[User],
    *,
    subgroup: int | None,
    student_id: UUID | None,
) -> list[User]:
    """Keep only students relevant for the requested export scope."""
    filtered_students = students
    if student_id is not None:
        filtered_students = [student for student in filtered_students if student.id == student_id]

    return filter_students_for_subgroup(filtered_students, subgroup)


def resolve_export_subgroup(
    students: list[User],
    *,
    subgroup: int | None,
    student_id: UUID | None,
) -> int | None:
    """Derive subgroup from the selected student when export scope is narrowed to one student."""
    if subgroup is not None:
        return subgroup

    if student_id is not None and len(students) == 1:
        return students[0].subgroup

    return None


def filter_lessons_for_subgroup(lessons: list[Lesson], subgroup: int | None) -> list[Lesson]:
    """Keep lessons visible for the selected subgroup."""
    if subgroup is None:
        return lessons

    return [lesson for lesson in lessons if lesson.subgroup is None or lesson.subgroup == subgroup]


async def load_export_lessons(
    db: AsyncSession,
    *,
    group_id: UUID,
    start_date: date,
    end_date: date,
    subgroup: int | None = None,
) -> list[Lesson]:
    """Load non-cancelled lessons for the export period."""
    filters = [
        Lesson.group_id == group_id,
        Lesson.date >= start_date,
        Lesson.date <= end_date,
        Lesson.is_cancelled.is_(False),
    ]
    if subgroup is not None:
        filters.append(or_(Lesson.subgroup.is_(None), Lesson.subgroup == subgroup))

    query = select(Lesson).where(and_(*filters)).order_by(Lesson.date, Lesson.lesson_number)
    result = await db.execute(query)
    lessons = list(result.scalars().all())
    logger.debug("Loaded %d export lessons for group %s subgroup %s", len(lessons), group_id, subgroup)
    return lessons


def build_lesson_export_columns(lessons: list[Lesson]) -> list[LessonExportColumn]:
    """Convert lesson models into export schema rows."""
    return [
        LessonExportColumn(
            lesson_id=lesson.id,
            date=lesson.date,
            lesson_number=lesson.lesson_number,
            lesson_type=lesson.lesson_type.value,
            topic=lesson.topic,
            work_number=lesson.work_number,
            subgroup=lesson.subgroup,
        )
        for lesson in lessons
    ]


async def collect_attendance_rows(
    db: AsyncSession,
    *,
    group_id: UUID,
    lessons: list[Lesson],
    students: list[User],
) -> list[AttendanceExportRow]:
    """Build export attendance rows from the shared attendance contract."""
    if not lessons or not students:
        logger.debug("Skipping export attendance rows: lessons=%d students=%d", len(lessons), len(students))
        return []

    attendance_by_student = await load_attendance_by_student_for_lessons(
        db,
        group_id=group_id,
        student_ids=[student.id for student in students],
        lessons=lessons,
    )
    snapshots = build_student_attendance_snapshots(
        students=students,
        lessons=lessons,
        attendance_records=[
            record
            for student_records in attendance_by_student.values()
            for record in student_records
        ],
    )

    rows: list[AttendanceExportRow] = []
    for student in students:
        stats = snapshot_to_report_stats(snapshots.get(student.id))
        attendance_by_date = {
            f"{record.date}_{record.lesson_number}": record.status.value
            for record in attendance_by_student.get(student.id, [])
        }
        rows.append(
            AttendanceExportRow(
                student_id=student.id,
                student_name=student.full_name,
                subgroup=student.subgroup,
                attendance_by_date=attendance_by_date,
                stats={
                    "present_count": int(stats["present"]),
                    "absent_count": int(stats["absent"]),
                    "late_count": int(stats["late"]),
                    "excused_count": int(stats["excused"]),
                    "total": int(stats["total"]),
                },
                attendance_rate=round(float(stats["rate"]), 2),
            )
        )

    logger.debug("Built %d export attendance rows for group %s", len(rows), group_id)
    return rows
