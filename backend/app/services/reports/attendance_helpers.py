"""Attendance helpers for public reports built on the shared attendance contract."""

from __future__ import annotations

from datetime import date
from typing import TypeAlias
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceStatus
from app.models.lesson import Lesson
from app.models.user import User
from app.schemas.report import AttendanceDistribution, AttendanceRecord, AttendanceStats, DateAttendance
from app.services.attendance_contract import (
    AttendanceCounts,
    StudentAttendanceSnapshot,
    build_student_attendance_snapshots,
    calculate_lesson_attendance_rate,
    calculate_report_attendance_rate,
    lesson_key,
    snapshot_to_report_stats,
)
from app.services.attendance_period import load_attendance_by_student_for_lessons, load_period_lessons

from .attendance_timeline_helpers import get_recent_lessons_history, get_today_lessons_attendance

AttendanceValueMap: TypeAlias = dict[str, int | float]
StudentAttendanceStatsMap: TypeAlias = dict[UUID, AttendanceValueMap]


def _status_key(status_value: object) -> str:
    return status_value.value.lower() if hasattr(status_value, "value") else str(status_value).lower()


async def load_group_attendance_snapshots(
    db: AsyncSession,
    group_id: UUID,
    students: list[User],
    *,
    period_start: date,
    period_end: date,
    subject_id: UUID | None = None,
) -> tuple[list[Lesson], dict[UUID, StudentAttendanceSnapshot]]:
    """Load relevant lessons and per-student attendance snapshots for a report period."""
    lessons = await load_period_lessons(
        db,
        group_id=group_id,
        period_start=period_start,
        period_end=period_end,
        subject_id=subject_id,
    )
    if not lessons or not students:
        return lessons, {}

    attendance_by_student = await load_attendance_by_student_for_lessons(
        db,
        group_id=group_id,
        student_ids=[student.id for student in students],
        lessons=lessons,
    )
    snapshots = build_student_attendance_snapshots(
        students=students,
        lessons=lessons,
        attendance_records=[record for student_records in attendance_by_student.values() for record in student_records],
    )
    return lessons, snapshots


def snapshot_to_stats(snapshot: StudentAttendanceSnapshot | None) -> AttendanceValueMap:
    return snapshot_to_report_stats(snapshot)


def build_group_attendance_stats(
    students: list[User],
    snapshots: dict[UUID, StudentAttendanceSnapshot],
) -> StudentAttendanceStatsMap:
    """Return per-student report attendance stats."""
    return {student.id: snapshot_to_stats(snapshots.get(student.id)) for student in students}


def build_attendance_distribution(
    snapshots: dict[UUID, StudentAttendanceSnapshot],
) -> AttendanceDistribution:
    """Aggregate report attendance statuses across all student lesson slots."""
    distribution = AttendanceDistribution()
    for snapshot in snapshots.values():
        distribution.present += snapshot.counts.present
        distribution.late += snapshot.counts.late
        distribution.excused += snapshot.counts.excused
        distribution.absent += snapshot.counts.absent
    return distribution


def build_attendance_by_subgroup(
    students: list[User],
    snapshots: dict[UUID, StudentAttendanceSnapshot],
) -> dict[str, AttendanceDistribution]:
    """Aggregate report attendance distribution per subgroup."""
    result: dict[str, AttendanceDistribution] = {}
    for subgroup in [1, 2]:
        subgroup_distribution = AttendanceDistribution()
        subgroup_students = [student for student in students if student.subgroup == subgroup]
        for student in subgroup_students:
            snapshot = snapshots.get(student.id)
            if snapshot is None:
                continue
            subgroup_distribution.present += snapshot.counts.present
            subgroup_distribution.late += snapshot.counts.late
            subgroup_distribution.excused += snapshot.counts.excused
            subgroup_distribution.absent += snapshot.counts.absent
        result[str(subgroup)] = subgroup_distribution
    return result


def build_full_attendance_stats(
    *,
    lessons: list[Lesson],
    students: list[User],
    snapshots: dict[UUID, StudentAttendanceSnapshot],
    has_subgroups: bool,
) -> AttendanceStats:
    """Build the full attendance stats payload from shared snapshots."""
    distribution = build_attendance_distribution(snapshots)
    average_rate = calculate_report_attendance_rate(
        counts=snapshots_total_counts(snapshots),
        expected_lessons=sum(snapshot.expected_lessons for snapshot in snapshots.values()),
    )
    return AttendanceStats(
        distribution=distribution,
        by_subgroup=build_attendance_by_subgroup(students, snapshots) if has_subgroups else {},
        trend=build_attendance_trend(lessons=lessons, students=students, snapshots=snapshots),
        average_rate=average_rate,
    )


def build_student_attendance_history(
    lessons: list[Lesson],
    snapshot: StudentAttendanceSnapshot | None,
) -> list[AttendanceRecord]:
    """Render period-aware attendance history from relevant lesson slots."""
    if snapshot is None:
        return []

    history: list[AttendanceRecord] = []
    sorted_lessons = sorted(lessons, key=lambda lesson: (lesson.date, lesson.lesson_number or 0), reverse=True)
    for lesson in sorted_lessons:
        key = lesson_key(lesson)
        status = snapshot.statuses_by_lesson_key.get(key, AttendanceStatus.ABSENT)
        lesson_type_str = lesson.lesson_type.value if hasattr(lesson.lesson_type, "value") else str(lesson.lesson_type)
        history.append(
            AttendanceRecord(
                date=lesson.date,
                status=_status_key(status),
                lesson_topic=lesson.topic,
                lesson_number=lesson.lesson_number,
                lesson_type=lesson_type_str,
                subgroup=lesson.subgroup,
            )
        )
    return history


def snapshots_total_counts(snapshots: dict[UUID, StudentAttendanceSnapshot]) -> AttendanceCounts:
    """Collapse snapshots into a single aggregate count set for rate calculations."""
    total_present = 0
    total_late = 0
    total_excused = 0
    total_absent = 0
    for snapshot in snapshots.values():
        total_present += snapshot.counts.present
        total_late += snapshot.counts.late
        total_excused += snapshot.counts.excused
        total_absent += snapshot.counts.absent
    return AttendanceCounts(
        present=total_present,
        late=total_late,
        excused=total_excused,
        absent=total_absent,
    )


def build_attendance_trend(
    *,
    lessons: list[Lesson],
    students: list[User],
    snapshots: dict[UUID, StudentAttendanceSnapshot],
    limit: int = 20,
) -> list[DateAttendance]:
    """Build lesson-level attendance trend from shared snapshots."""
    trend: list[DateAttendance] = []
    sorted_lessons = sorted(lessons, key=lambda lesson: (lesson.date, lesson.lesson_number or 0))
    for lesson in sorted_lessons[-limit:]:
        key = lesson_key(lesson)
        relevant_students = (
            students
            if lesson.subgroup is None
            else [student for student in students if student.subgroup == lesson.subgroup]
        )
        present_count = 0
        for student in relevant_students:
            snapshot = snapshots.get(student.id)
            if snapshot is None:
                continue
            status = snapshot.statuses_by_lesson_key.get(key, AttendanceStatus.ABSENT)
            if status in {AttendanceStatus.PRESENT, AttendanceStatus.LATE}:
                present_count += 1
        trend.append(
            DateAttendance(
                date=lesson.date.isoformat(),
                rate=calculate_lesson_attendance_rate(
                    present_count=present_count,
                    late_count=0,
                    total_count=len(relevant_students),
                ),
                subgroup=lesson.subgroup,
            )
        )
    return trend
