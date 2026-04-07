"""Unit tests for admin schedule attendance summaries."""

from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.services.schedule_attendance_summary import (
    calculate_grouped_lecture_attendance_summary,
    calculate_lesson_attendance_summary,
    is_schedule_slot_past,
)


def _student(*, group_id, subgroup: int | None, student_id=None):
    return SimpleNamespace(
        id=student_id or uuid4(),
        group_id=group_id,
        subgroup=subgroup,
        is_active=True,
        full_name="Student",
    )


def _lesson(
    *,
    group_id,
    lesson_date: date,
    lesson_number: int,
    subgroup: int | None = None,
    is_cancelled: bool = False,
    ended_early: bool = False,
):
    return SimpleNamespace(
        id=uuid4(),
        group_id=group_id,
        date=lesson_date,
        lesson_number=lesson_number,
        subgroup=subgroup,
        is_cancelled=is_cancelled,
        ended_early=ended_early,
    )


def test_regular_lesson_summary_uses_only_relevant_subgroup_students():
    group_id = uuid4()
    subgroup_one_marked = _student(group_id=group_id, subgroup=1)
    subgroup_one_unmarked = _student(group_id=group_id, subgroup=1)
    subgroup_two = _student(group_id=group_id, subgroup=2)
    lesson = _lesson(group_id=group_id, lesson_date=date(2026, 4, 1), lesson_number=2, subgroup=1)

    summary = calculate_lesson_attendance_summary(
        lesson,
        [subgroup_one_marked, subgroup_one_unmarked, subgroup_two],
        {subgroup_one_marked.id, subgroup_two.id},
        current_time=datetime(2026, 4, 1, 12, 0),
    )

    assert summary.state == "partial"
    assert summary.marked_count == 1
    assert summary.expected_count == 2
    assert summary.is_past is True


def test_cancelled_lesson_summary_is_not_applicable():
    group_id = uuid4()
    student = _student(group_id=group_id, subgroup=None)
    lesson = _lesson(
        group_id=group_id,
        lesson_date=date(2026, 4, 1),
        lesson_number=1,
        is_cancelled=True,
    )

    summary = calculate_lesson_attendance_summary(
        lesson,
        [student],
        {student.id},
        current_time=datetime(2026, 4, 1, 11, 0),
    )

    assert summary.state == "not_applicable"
    assert summary.marked_count == 0
    assert summary.expected_count == 0
    assert summary.is_past is True


def test_future_lesson_summary_is_hidden_until_pair_ends():
    group_id = uuid4()
    student = _student(group_id=group_id, subgroup=None)
    lesson = _lesson(group_id=group_id, lesson_date=date(2026, 4, 6), lesson_number=2)

    summary = calculate_lesson_attendance_summary(
        lesson,
        [student],
        set(),
        current_time=datetime(2026, 4, 6, 11, 0),
    )

    assert summary.state == "hidden"
    assert summary.marked_count == 0
    assert summary.expected_count == 1
    assert summary.is_past is False


def test_future_cancelled_lesson_stays_hidden_until_pair_ends():
    group_id = uuid4()
    student = _student(group_id=group_id, subgroup=None)
    lesson = _lesson(
        group_id=group_id,
        lesson_date=date(2026, 4, 6),
        lesson_number=2,
        is_cancelled=True,
    )

    summary = calculate_lesson_attendance_summary(
        lesson,
        [student],
        set(),
        current_time=datetime(2026, 4, 6, 11, 0),
    )

    assert summary.state == "hidden"
    assert summary.is_past is False


def test_grouped_lecture_summary_skips_cancelled_rows_and_deduplicates_students():
    group_a = uuid4()
    group_b = uuid4()
    shared_student_id = uuid4()
    group_a_active = _lesson(group_id=group_a, lesson_date=date(2026, 4, 2), lesson_number=3)
    group_b_cancelled = _lesson(
        group_id=group_b,
        lesson_date=date(2026, 4, 2),
        lesson_number=3,
        is_cancelled=True,
        ended_early=True,
    )

    students_by_group = {
        group_a: [
            _student(group_id=group_a, subgroup=None, student_id=shared_student_id),
            _student(group_id=group_a, subgroup=None),
        ],
        group_b: [
            _student(group_id=group_b, subgroup=None, student_id=shared_student_id),
            _student(group_id=group_b, subgroup=None),
        ],
    }

    result = calculate_grouped_lecture_attendance_summary(
        [group_a_active, group_b_cancelled],
        students_by_group,
        {
            group_a_active.id: {shared_student_id},
            group_b_cancelled.id: {shared_student_id},
        },
        current_time=datetime(2026, 4, 2, 14, 0),
    )

    assert result.is_cancelled is False
    assert result.ended_early is False
    assert result.summary.state == "partial"
    assert result.summary.marked_count == 1
    assert result.summary.expected_count == 2
    assert result.summary.is_past is True


def test_grouped_lecture_summary_all_cancelled_is_not_applicable():
    group_id = uuid4()
    cancelled_lesson = _lesson(
        group_id=group_id,
        lesson_date=date(2026, 4, 2),
        lesson_number=4,
        is_cancelled=True,
    )

    result = calculate_grouped_lecture_attendance_summary(
        [cancelled_lesson],
        {group_id: [_student(group_id=group_id, subgroup=None)]},
        {cancelled_lesson.id: set()},
        current_time=datetime(2026, 4, 2, 16, 0),
    )

    assert result.is_cancelled is True
    assert result.ended_early is False
    assert result.summary.state == "not_applicable"
    assert result.summary.marked_count == 0
    assert result.summary.expected_count == 0
    assert result.summary.is_past is True


def test_slot_past_uses_lesson_end_time_for_today():
    assert is_schedule_slot_past(date(2026, 4, 6), 2, datetime(2026, 4, 6, 11, 41)) is True
    assert is_schedule_slot_past(date(2026, 4, 6), 2, datetime(2026, 4, 6, 11, 40)) is False
