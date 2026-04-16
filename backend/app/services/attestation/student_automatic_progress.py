"""Student automatic-pass status resolved from offerings and queue state."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.attestation.automatic_queue import (
    list_offering_automatic_queue,
    offering_allows_automatic,
    resolve_student_automatic_offering,
)


@dataclass(frozen=True)
class StudentAutomaticProgress:
    completed_count: int
    automatic_remaining: int
    queue_position: int | None
    is_winner: bool | None
    completion_at: datetime | None
    automatic_reason: str | None
    automatic_declined: bool


async def resolve_student_automatic_progress(
    db: AsyncSession,
    *,
    student: User,
    subject_id: UUID | None,
    total_labs: int,
    automatic_places: int | None,
    automatic_enabled: bool,
) -> StudentAutomaticProgress:
    if total_labs <= 0:
        return StudentAutomaticProgress(0, 0, None, None, None, "total_missing", False)

    if not automatic_enabled:
        return StudentAutomaticProgress(0, total_labs, None, None, None, "disabled", False)

    offering_resolution = await resolve_student_automatic_offering(
        db,
        student=student,
        subject_id=subject_id,
    )
    if offering_resolution.offering is None:
        return StudentAutomaticProgress(0, total_labs, None, None, None, offering_resolution.reason, False)

    if not offering_allows_automatic(offering_resolution.offering):
        return StudentAutomaticProgress(0, total_labs, None, None, None, "not_exam", False)

    entries = await list_offering_automatic_queue(
        db,
        offering=offering_resolution.offering,
        total_labs=total_labs,
        automatic_places=automatic_places,
    )
    current_entry = next((entry for entry in entries if entry.student_id == student.id), None)
    if current_entry is None:
        return StudentAutomaticProgress(0, total_labs, None, None, None, "student_missing", False)

    reason = "refused" if current_entry.is_declined else None
    return StudentAutomaticProgress(
        completed_count=current_entry.completed_count,
        automatic_remaining=current_entry.automatic_remaining,
        queue_position=current_entry.queue_position,
        is_winner=current_entry.is_winner,
        completion_at=current_entry.completion_at,
        automatic_reason=reason,
        automatic_declined=current_entry.is_declined,
    )
