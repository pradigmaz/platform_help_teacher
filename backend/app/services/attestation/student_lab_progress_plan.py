"""Derived student-facing lab thresholds for attestation and automatic pass."""

from datetime import datetime
from typing import Any


def build_student_lab_progress_plan(
    *,
    total_labs: int,
    first_required: int,
    second_required: int,
    automatic_enabled: bool,
    automatic_places: int | None,
    completed_count: int = 0,
    automatic_remaining: int | None = None,
    automatic_queue_position: int | None = None,
    automatic_is_winner: bool | None = None,
    automatic_completion_at: datetime | None = None,
    automatic_reason: str | None = None,
    automatic_declined: bool = False,
) -> dict[str, Any]:
    """Build a student-facing plan from manual lab thresholds."""
    second_total_required = first_required + second_required
    automatic_extra_required = max(total_labs - second_total_required, 0)
    resolved_automatic_remaining = automatic_remaining
    if resolved_automatic_remaining is None:
        resolved_automatic_remaining = max(total_labs - completed_count, 0)

    return {
        "total_required": total_labs,
        "first_required": first_required,
        "second_extra_required": second_required,
        "second_total_required": second_total_required,
        "automatic_extra_required": automatic_extra_required,
        "automatic_enabled": automatic_enabled,
        "automatic_places": automatic_places,
        "completed_count": completed_count,
        "automatic_remaining": resolved_automatic_remaining,
        "automatic_queue_position": automatic_queue_position,
        "automatic_is_winner": automatic_is_winner,
        "automatic_completion_at": automatic_completion_at.isoformat() if automatic_completion_at else None,
        "automatic_reason": automatic_reason,
        "automatic_declined": automatic_declined,
    }
