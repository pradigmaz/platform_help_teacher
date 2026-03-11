"""Helpers for normalized lab progress calculations."""

from collections.abc import Iterable
from typing import Any
from uuid import UUID

from app.models.lesson_grade import LessonGrade


def is_completed_lab_grade(grade: int | None) -> bool:
    """A lab counts as completed only for grades above 2."""
    return grade is not None and grade > 2


def _lesson_grade_rank(grade: LessonGrade) -> tuple[int, str, str]:
    updated_at = getattr(grade, "updated_at", None) or getattr(grade, "created_at", None)
    updated_at_str = updated_at.isoformat() if updated_at else ""
    return (grade.grade, updated_at_str, str(grade.id))


def _transfer_grade_rank(grade_data: dict[str, Any], index: int) -> tuple[int, str, int]:
    created_at = str(grade_data.get("updated_at") or grade_data.get("created_at") or "")
    return (int(grade_data.get("grade") or 0), created_at, index)


def get_lesson_grade_subject_key(grade: LessonGrade) -> str:
    """Return the subject key stored on a grade after deduplication."""
    return str(getattr(grade, "lab_subject_id", None) or grade.lesson_id)


def dedupe_lesson_grade_rows(rows: Iterable[tuple[LessonGrade, UUID | None]]) -> list[LessonGrade]:
    """Keep the best row per (subject_id, work_number).

    Side-effect: sets ``lab_subject_id`` on each returned LessonGrade so that
    downstream code (e.g. lab_calculator) can access the subject without an
    extra join.
    """
    best_by_key: dict[tuple[str, int], tuple[LessonGrade, UUID | None]] = {}

    for grade, subject_id in rows:
        if grade.work_number is None:
            continue

        key = (str(subject_id or grade.lesson_id), grade.work_number)
        current = best_by_key.get(key)

        if current is None or _lesson_grade_rank(grade) > _lesson_grade_rank(current[0]):
            best_by_key[key] = (grade, subject_id)

    result: list[LessonGrade] = []
    for grade, subject_id in best_by_key.values():
        grade.lab_subject_id = subject_id  # type: ignore[attr-defined]
        result.append(grade)
    return result


def dedupe_transfer_lab_grades(transfer_grades: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Keep the best transfer snapshot per (subject_id, work_number)."""
    if not transfer_grades:
        return []

    best_by_work: dict[tuple[str, int], tuple[dict[str, Any], int]] = {}
    for index, grade_data in enumerate(transfer_grades):
        work_number = grade_data.get("work_number")
        if work_number is None:
            continue

        subject_key = str(grade_data.get("subject_id") or "__legacy__")
        key = (subject_key, int(work_number))
        current = best_by_work.get(key)
        if current is None or _transfer_grade_rank(grade_data, index) > _transfer_grade_rank(*current):
            best_by_work[key] = (grade_data, index)

    return [item[0] for item in best_by_work.values()]
