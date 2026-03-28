"""Unified deadline evaluation engine for student and teacher read paths."""

from dataclasses import dataclass
from datetime import date

from app.services.deadline_context import DeadlineContext
from app.services.deadline_semantics import DeadlineVisibilityState, evaluate_deadline_state
from app.services.deadline_trace import DeadlineTrace, build_deadline_trace_from_state


@dataclass(frozen=True)
class DeadlineEvaluation:
    """Single source of truth for deadline context, state and trace."""

    context: DeadlineContext
    state: DeadlineVisibilityState
    trace: DeadlineTrace


def evaluate_deadline_context(
    *,
    context: DeadlineContext,
    deadline_5_lessons: int | None,
    deadline_4_lessons: int | None,
    visible_from: date | None = None,
    today: date | None = None,
    effective_deadline_5_date: date | None = None,
    effective_deadline_4_date: date | None = None,
) -> DeadlineEvaluation:
    """Build shared deadline state/trace from a pre-resolved context."""
    state = evaluate_deadline_state(
        lesson_index=context.lesson_index or 0,
        deadline_5_lessons=deadline_5_lessons,
        deadline_4_lessons=deadline_4_lessons,
        extension_bonus=context.extension_bonus,
        is_excused_origin=context.is_excused_origin,
        visible_from=visible_from,
        today=today,
    )
    trace = build_deadline_trace_from_state(
        context=context,
        state=state,
        deadline_5_lessons=deadline_5_lessons,
        deadline_4_lessons=deadline_4_lessons,
        effective_deadline_5_date=effective_deadline_5_date,
        effective_deadline_4_date=effective_deadline_4_date,
    )
    return DeadlineEvaluation(context=context, state=state, trace=trace)
