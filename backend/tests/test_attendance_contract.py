"""Invariant tests for the shared attendance contract."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from uuid import uuid4

from app.models.attendance import AttendanceStatus
from app.services.attendance_contract import (
    AttendanceCounts,
    build_student_attendance_snapshots,
    calculate_lesson_attendance_rate,
    calculate_report_attendance_rate,
    snapshot_to_report_stats,
)


def _student(*, subgroup: int | None):
    return SimpleNamespace(id=uuid4(), subgroup=subgroup, full_name="Test Student")


def _lesson(*, lesson_date: date, lesson_number: int, subgroup: int | None):
    return SimpleNamespace(
        id=uuid4(),
        date=lesson_date,
        lesson_number=lesson_number,
        subgroup=subgroup,
    )


def _attendance(*, student_id, lesson, status: AttendanceStatus):
    return SimpleNamespace(
        student_id=student_id,
        lesson_id=lesson.id,
        date=lesson.date,
        lesson_number=lesson.lesson_number,
        status=status,
    )


def test_report_rate_treats_missing_relevant_records_as_absent():
    student = _student(subgroup=1)
    lecture = _lesson(lesson_date=date(2026, 3, 2), lesson_number=1, subgroup=None)
    subgroup_lab = _lesson(lesson_date=date(2026, 3, 4), lesson_number=2, subgroup=1)

    snapshots = build_student_attendance_snapshots(
        students=[student],
        lessons=[lecture, subgroup_lab],
        attendance_records=[
            _attendance(student_id=student.id, lesson=lecture, status=AttendanceStatus.PRESENT),
        ],
    )

    stats = snapshot_to_report_stats(snapshots[student.id])
    assert stats == {
        "present": 1,
        "late": 0,
        "excused": 0,
        "absent": 1,
        "total": 2,
        "rate": 50.0,
    }


def test_report_rate_uses_only_relevant_subgroup_lessons():
    student = _student(subgroup=1)
    lecture = _lesson(lesson_date=date(2026, 3, 2), lesson_number=1, subgroup=None)
    subgroup_one_lab = _lesson(lesson_date=date(2026, 3, 4), lesson_number=2, subgroup=1)
    subgroup_two_lab = _lesson(lesson_date=date(2026, 3, 5), lesson_number=2, subgroup=2)

    snapshots = build_student_attendance_snapshots(
        students=[student],
        lessons=[lecture, subgroup_one_lab, subgroup_two_lab],
        attendance_records=[
            _attendance(student_id=student.id, lesson=lecture, status=AttendanceStatus.PRESENT),
            _attendance(student_id=student.id, lesson=subgroup_one_lab, status=AttendanceStatus.LATE),
        ],
    )

    stats = snapshot_to_report_stats(snapshots[student.id])
    assert stats["total"] == 2
    assert stats["absent"] == 0
    assert stats["rate"] == 75.0


def test_report_rate_all_excused_is_full_credit():
    counts = AttendanceCounts(excused=3)
    assert calculate_report_attendance_rate(counts, expected_lessons=3) == 100.0


def test_lesson_attendance_rate_is_intentionally_separate_metric():
    assert calculate_lesson_attendance_rate(present_count=1, late_count=1, total_count=4) == 50.0
