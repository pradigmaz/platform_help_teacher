"""Shared read-model normalization for lab submission progress."""

from dataclasses import dataclass
from datetime import datetime

from app.models.lesson_grade import LessonGrade
from app.models.submission import Submission, SubmissionStatus
from app.services.student_lab_service import resolve_lab_acceptance


@dataclass(frozen=True)
class NormalizedLabProgress:
    """Normalized lab progress shared by admin/student read paths."""

    normalized_status: str | None
    grade: int | None
    acceptance_source: str | None
    submitted_at: datetime | None
    feedback: str | None


def normalize_lab_progress(
    submission: Submission | None,
    journal_grade: LessonGrade | None,
) -> NormalizedLabProgress:
    """Collapse legacy and current submission states into one read model."""
    is_accepted, journal_grade_value, acceptance_source = resolve_lab_acceptance(submission, journal_grade)
    submitted_at = None
    feedback = submission.feedback if submission is not None else None
    if submission is not None:
        submitted_at = submission.ready_at or submission.accepted_at or submission.created_at

    if is_accepted:
        return NormalizedLabProgress(
            normalized_status=SubmissionStatus.ACCEPTED.value,
            grade=journal_grade_value if journal_grade_value is not None else submission.grade if submission else None,
            acceptance_source=acceptance_source,
            submitted_at=submitted_at,
            feedback=feedback,
        )

    if journal_grade_value == 2:
        return NormalizedLabProgress(
            normalized_status=SubmissionStatus.REJECTED.value,
            grade=2,
            acceptance_source=None,
            submitted_at=submitted_at,
            feedback=feedback,
        )

    if submission is None:
        return NormalizedLabProgress(
            normalized_status=None,
            grade=None,
            acceptance_source=None,
            submitted_at=None,
            feedback=None,
        )

    if submission.status in (SubmissionStatus.READY, SubmissionStatus.IN_REVIEW):
        normalized_status = SubmissionStatus.READY.value
        grade = None
    elif submission.status in (SubmissionStatus.REJECTED, SubmissionStatus.REQ_CHANGES):
        normalized_status = SubmissionStatus.REJECTED.value
        grade = submission.grade
    else:
        normalized_status = None
        grade = None

    return NormalizedLabProgress(
        normalized_status=normalized_status,
        grade=grade,
        acceptance_source=None,
        submitted_at=submitted_at,
        feedback=feedback,
    )
