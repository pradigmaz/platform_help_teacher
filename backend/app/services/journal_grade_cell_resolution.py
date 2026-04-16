"""Resolve grade rows inside one lesson/student journal cell."""

from collections.abc import Iterable
from uuid import UUID

from app.models import LessonGrade


class GradeCellResolutionConflict(ValueError):
    """Raised when a lesson/student grade cell cannot be addressed safely."""


def select_grade_for_work(
    lesson_id: UUID,
    student_id: UUID,
    grades: Iterable[LessonGrade],
    work_number: int | None,
) -> LessonGrade | None:
    """Return the row addressed by ``work_number`` or fail on legacy ambiguity."""
    cell_grades = list(grades)
    if not cell_grades:
        return None

    if len(cell_grades) == 1:
        grade = cell_grades[0]
        if work_number is None or grade.work_number is None or grade.work_number == work_number:
            return grade
        return None

    if work_number is None:
        raise GradeCellResolutionConflict(_conflict_message(lesson_id, student_id, cell_grades))

    if any(grade.work_number is None for grade in cell_grades):
        raise GradeCellResolutionConflict(_conflict_message(lesson_id, student_id, cell_grades))

    matching_grades = [grade for grade in cell_grades if grade.work_number == work_number]
    if len(matching_grades) > 1:
        raise GradeCellResolutionConflict(_conflict_message(lesson_id, student_id, cell_grades))
    return matching_grades[0] if matching_grades else None


def _conflict_message(lesson_id: UUID, student_id: UUID, grades: list[LessonGrade]) -> str:
    return (
        f"Конфликт legacy-данных: у студента {student_id} уже {len(grades)} оценок "
        f"на занятии {lesson_id}. Сначала разрешите конфликт."
    )
