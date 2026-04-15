"""Serialize lesson grade cells for journal and schedule views."""

from __future__ import annotations

from typing import TypedDict

from app.models import LessonGrade


class GradeItemSummary(TypedDict):
    grade: int
    work_number: int | None


class GradeCellSummary(TypedDict):
    grade: int | None
    work_number: int | None
    has_conflict: bool
    conflict_count: int
    grade_items: list[GradeItemSummary]


def summarize_lesson_grade_cell(rows: list[LessonGrade]) -> GradeCellSummary:
    """Return a cell payload, treating distinct work numbers as normal multi-grade data."""
    ordered_rows = sorted(rows, key=lambda row: (row.work_number is None, row.work_number or 0, str(row.id)))
    grade_items: list[GradeItemSummary] = [
        {
            "grade": row.grade,
            "work_number": row.work_number,
        }
        for row in ordered_rows
    ]
    work_numbers = [row.work_number for row in ordered_rows]
    has_conflict = any(work_number is None for work_number in work_numbers) or len(set(work_numbers)) != len(
        work_numbers
    )
    first = ordered_rows[0]

    return {
        "grade": None if has_conflict else first.grade,
        "work_number": None if has_conflict else first.work_number,
        "has_conflict": has_conflict,
        "conflict_count": len(ordered_rows) if has_conflict else 0,
        "grade_items": grade_items,
    }
