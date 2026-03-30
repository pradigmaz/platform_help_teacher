"""Helpers for normalized lab progress calculations."""

from collections.abc import Iterable
from typing import Any
from uuid import UUID

from sqlalchemy.engine import Row

from app.models.lesson_grade import LessonGrade
from app.models.submission import Submission


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


def _submission_grade_rank(submission: Submission) -> tuple[int, str, str]:
    accepted_at = getattr(submission, "accepted_at", None) or getattr(submission, "updated_at", None)
    accepted_at_str = accepted_at.isoformat() if accepted_at else ""
    return (int(submission.grade or 0), accepted_at_str, str(submission.id))


def get_lesson_grade_subject_key(grade: LessonGrade) -> str:
    """Return the subject key stored on a grade after deduplication."""
    return str(getattr(grade, "lab_subject_id", None) or grade.lesson_id)


LessonGradeRow = tuple[LessonGrade, UUID | None]


def dedupe_lesson_grade_rows(rows: Iterable[LessonGradeRow | Row[LessonGradeRow]]) -> list[LessonGrade]:
    """Keep the best row per (subject_id, work_number).

    Side-effect: sets ``lab_subject_id`` on each returned LessonGrade so that
    downstream code (e.g. lab_calculator) can access the subject without an
    extra join.
    """
    best_by_key: dict[tuple[str, int], tuple[LessonGrade, UUID | None]] = {}

    for row in rows:
        grade, subject_id = row
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


def dedupe_submission_lab_grades(rows: Iterable[tuple[Submission, UUID | None, int | None]]) -> list[dict[str, Any]]:
    """Keep the best accepted submission per (subject_id, work_number)."""
    best_by_key: dict[tuple[str, int], Submission] = {}

    for submission, subject_id, work_number in rows:
        if work_number is None or submission.grade is None:
            continue

        key = (str(subject_id or "__legacy__"), int(work_number))
        current = best_by_key.get(key)
        if current is None or _submission_grade_rank(submission) > _submission_grade_rank(current):
            best_by_key[key] = submission

    result: list[dict[str, Any]] = []
    for (subject_key, work_number), submission in best_by_key.items():
        grade_value = submission.grade
        if grade_value is None:
            continue
        result.append(
            {
                "submission_id": str(submission.id),
                "lesson_id": str(submission.lesson_id) if submission.lesson_id else None,
                "subject_id": subject_key,
                "work_number": work_number,
                "grade": int(grade_value),
                "accepted_at": submission.accepted_at.isoformat() if submission.accepted_at else None,
                "created_at": submission.created_at.isoformat() if submission.created_at else None,
            }
        )
    return result
