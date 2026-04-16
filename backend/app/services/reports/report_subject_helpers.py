"""Subject-selection helpers for public report flows."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attestation_settings import AttestationSettings
from app.models.subject import Subject
from app.services.attestation.subject_scope import list_group_subject_options_in_period


@dataclass(frozen=True)
class ReportSubjectContext:
    available_subjects: list[Subject]
    selected_subject_id: UUID | None
    subject_name: str | None
    requires_subject: bool


async def resolve_report_subject_context(
    db: AsyncSession,
    *,
    group_id: UUID,
    settings: AttestationSettings,
    requested_subject_id: UUID | None,
) -> ReportSubjectContext:
    """Resolve report subject selection without raising when the choice is missing."""

    available_subjects = await list_group_subject_options_in_period(db, group_id, settings)
    available_by_id = {subject.id: subject for subject in available_subjects}

    if requested_subject_id is not None and requested_subject_id in available_by_id:
        selected_subject_id = requested_subject_id
    elif len(available_subjects) == 1:
        selected_subject_id = available_subjects[0].id
    else:
        selected_subject_id = None

    selected_subject = available_by_id.get(selected_subject_id) if selected_subject_id is not None else None
    return ReportSubjectContext(
        available_subjects=available_subjects,
        selected_subject_id=selected_subject_id,
        subject_name=selected_subject.name if selected_subject is not None else None,
        requires_subject=len(available_subjects) > 1,
    )
