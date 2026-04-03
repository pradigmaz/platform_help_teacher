"""Shared read model for traceable deadline state."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

from app.services.deadline_context import DeadlineContext
from app.services.deadline_semantics import DeadlineVisibilityState, apply_extension_bonus

if TYPE_CHECKING:
    from app.services.lab_visibility.models import LabVisibilityInfo


@dataclass(frozen=True)
class DeadlineTrace:
    """Stable deadline trace exposed to teacher/student read paths."""

    lesson_index: int | None
    current_max_grade: int
    extension_bonus: int
    has_extension: bool
    is_excused_origin: bool
    deadline_5_lessons: int | None
    deadline_4_lessons: int | None
    effective_deadline_5_lessons: int | None
    effective_deadline_4_lessons: int | None
    effective_deadline_5_date: date | None = None
    effective_deadline_4_date: date | None = None
    deadline_5_status: str | None = None
    deadline_4_status: str | None = None
    lessons_until_deadline_5: int | None = None
    lessons_until_deadline_4: int | None = None


def resolve_effective_deadline_date(
    *,
    ordered_lessons: Sequence[tuple[int | None, date]],
    lab_number: int,
    effective_deadline_lessons: int | None,
) -> date | None:
    """Resolve the last lesson date where a concrete max grade is still valid."""
    if effective_deadline_lessons is None:
        return None

    origin_index = next(
        (idx for idx, (work_number, _) in enumerate(ordered_lessons) if work_number == lab_number),
        None,
    )
    if origin_index is None:
        return None

    deadline_index = origin_index + effective_deadline_lessons
    if deadline_index < 0 or deadline_index >= len(ordered_lessons):
        return None

    return ordered_lessons[deadline_index][1]


def build_deadline_trace(
    *,
    lesson_index: int | None,
    current_max_grade: int,
    extension_bonus: int,
    is_excused_origin: bool,
    deadline_5_lessons: int | None,
    deadline_4_lessons: int | None,
    effective_deadline_5_date: date | None = None,
    effective_deadline_4_date: date | None = None,
    deadline_5_status: str | None = None,
    deadline_4_status: str | None = None,
    lessons_until_deadline_5: int | None = None,
    lessons_until_deadline_4: int | None = None,
) -> DeadlineTrace:
    """Build a normalized deadline trace from already computed state."""
    return DeadlineTrace(
        lesson_index=lesson_index,
        current_max_grade=current_max_grade,
        extension_bonus=extension_bonus,
        has_extension=extension_bonus > 0,
        is_excused_origin=is_excused_origin,
        deadline_5_lessons=deadline_5_lessons,
        deadline_4_lessons=deadline_4_lessons,
        effective_deadline_5_lessons=apply_extension_bonus(deadline_5_lessons, extension_bonus),
        effective_deadline_4_lessons=apply_extension_bonus(deadline_4_lessons, extension_bonus),
        effective_deadline_5_date=effective_deadline_5_date,
        effective_deadline_4_date=effective_deadline_4_date,
        deadline_5_status=deadline_5_status,
        deadline_4_status=deadline_4_status,
        lessons_until_deadline_5=lessons_until_deadline_5,
        lessons_until_deadline_4=lessons_until_deadline_4,
    )


def build_deadline_trace_from_state(
    *,
    context: DeadlineContext,
    state: DeadlineVisibilityState,
    deadline_5_lessons: int | None,
    deadline_4_lessons: int | None,
    effective_deadline_5_date: date | None = None,
    effective_deadline_4_date: date | None = None,
) -> DeadlineTrace:
    """Convert shared deadline context/state into API-friendly trace."""
    return build_deadline_trace(
        lesson_index=context.lesson_index,
        current_max_grade=state.current_max_grade,
        extension_bonus=context.extension_bonus,
        is_excused_origin=context.is_excused_origin,
        deadline_5_lessons=deadline_5_lessons,
        deadline_4_lessons=deadline_4_lessons,
        effective_deadline_5_date=effective_deadline_5_date,
        effective_deadline_4_date=effective_deadline_4_date,
        deadline_5_status=state.deadline_5_status,
        deadline_4_status=state.deadline_4_status,
        lessons_until_deadline_5=state.lessons_until_deadline_5,
        lessons_until_deadline_4=state.lessons_until_deadline_4,
    )


def build_deadline_trace_from_visibility_info(
    *,
    visibility_info: "LabVisibilityInfo",
    deadline_5_lessons: int | None,
    deadline_4_lessons: int | None,
) -> DeadlineTrace:
    """Build the same trace object from student-side visibility info."""
    return build_deadline_trace(
        lesson_index=visibility_info.lesson_index,
        current_max_grade=visibility_info.current_max_grade,
        extension_bonus=visibility_info.extension_bonus,
        is_excused_origin=visibility_info.is_excused_origin,
        deadline_5_lessons=deadline_5_lessons,
        deadline_4_lessons=deadline_4_lessons,
        effective_deadline_5_date=visibility_info.effective_deadline_5_date,
        effective_deadline_4_date=visibility_info.effective_deadline_4_date,
        deadline_5_status=visibility_info.deadline_5_status,
        deadline_4_status=visibility_info.deadline_4_status,
        lessons_until_deadline_5=visibility_info.lessons_until_deadline_5,
        lessons_until_deadline_4=visibility_info.lessons_until_deadline_4,
    )
