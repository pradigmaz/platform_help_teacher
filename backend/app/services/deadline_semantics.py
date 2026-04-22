"""Shared legacy deadline semantics for student and teacher paths."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DeadlineVisibilityState:
    deadline_5_status: str | None
    deadline_4_status: str | None
    lessons_until_deadline_5: int | None
    lessons_until_deadline_4: int | None
    current_max_grade: int
    lesson_index: int


def apply_extension_bonus(deadline_lessons: int | None, bonus_lessons: int) -> int | None:
    """Apply active extension bonus to a deadline threshold."""
    if deadline_lessons is None:
        return None
    return deadline_lessons + bonus_lessons


def evaluate_deadline_state(
    *,
    lesson_index: int,
    deadline_5_lessons: int | None,
    deadline_4_lessons: int | None,
    extension_bonus: int = 0,
    is_excused_origin: bool = False,
    deadline_active: bool = True,
    visible_from: date | None = None,
    today: date | None = None,
) -> DeadlineVisibilityState:
    """Shared deadline evaluation DTO for teacher-side validation and student-side read paths."""
    if is_excused_origin:
        return DeadlineVisibilityState(
            deadline_5_status=None,
            deadline_4_status=None,
            lessons_until_deadline_5=None,
            lessons_until_deadline_4=None,
            current_max_grade=5,
            lesson_index=lesson_index,
        )
    if not deadline_active:
        return DeadlineVisibilityState(
            deadline_5_status=None,
            deadline_4_status=None,
            lessons_until_deadline_5=None,
            lessons_until_deadline_4=None,
            current_max_grade=5,
            lesson_index=lesson_index,
        )

    effective_deadline_5 = apply_extension_bonus(deadline_5_lessons, extension_bonus)
    effective_deadline_4 = apply_extension_bonus(deadline_4_lessons, extension_bonus)

    if visible_from is not None and today is not None:
        deadline_5_status, lessons_until_5 = _calculate_deadline_status(
            lessons_after=lesson_index,
            effective_deadline=effective_deadline_5,
            visible_from=visible_from,
            today=today,
        )
        deadline_4_status, lessons_until_4 = _calculate_deadline_status(
            lessons_after=lesson_index,
            effective_deadline=effective_deadline_4,
            visible_from=visible_from,
            today=today,
        )
    else:
        deadline_5_status, lessons_until_5 = None, None
        deadline_4_status, lessons_until_4 = None, None

    current_max_grade = 5
    if effective_deadline_4 is not None and lesson_index > effective_deadline_4:
        current_max_grade = 3
    elif effective_deadline_5 is not None and lesson_index > effective_deadline_5:
        current_max_grade = 4

    return DeadlineVisibilityState(
        deadline_5_status=deadline_5_status,
        deadline_4_status=deadline_4_status,
        lessons_until_deadline_5=lessons_until_5,
        lessons_until_deadline_4=lessons_until_4,
        current_max_grade=current_max_grade,
        lesson_index=lesson_index,
    )


def max_allowed_grade_for_lesson_index(
    lesson_index: int,
    deadline_5_lessons: int | None,
    deadline_4_lessons: int | None,
    *,
    extension_bonus: int = 0,
    is_excused_origin: bool = False,
    deadline_active: bool = True,
) -> int:
    """Teacher-side max grade semantics shared by single and batch validators."""
    return evaluate_deadline_state(
        lesson_index=lesson_index,
        deadline_5_lessons=deadline_5_lessons,
        deadline_4_lessons=deadline_4_lessons,
        extension_bonus=extension_bonus,
        is_excused_origin=is_excused_origin,
        deadline_active=deadline_active,
    ).current_max_grade


def calculate_visibility_state(
    *,
    lessons_after: int,
    visible_from: date,
    today: date,
    deadline_5_lessons: int | None,
    deadline_4_lessons: int | None,
    extension_bonus: int = 0,
    is_excused_origin: bool = False,
    deadline_active: bool = True,
) -> DeadlineVisibilityState:
    """Student-side deadline view derived from the same lesson-index semantics."""
    return evaluate_deadline_state(
        lesson_index=lessons_after,
        deadline_5_lessons=deadline_5_lessons,
        deadline_4_lessons=deadline_4_lessons,
        extension_bonus=extension_bonus,
        is_excused_origin=is_excused_origin,
        deadline_active=deadline_active,
        visible_from=visible_from,
        today=today,
    )


def _calculate_deadline_status(
    *,
    lessons_after: int,
    effective_deadline: int | None,
    visible_from: date,
    today: date,
) -> tuple[str | None, int | None]:
    """Visibility status for a concrete effective deadline threshold."""
    if effective_deadline is None:
        return None, None
    if lessons_after > effective_deadline:
        return "expired", None
    if visible_from <= today:
        return "active", effective_deadline - lessons_after
    return None, None
