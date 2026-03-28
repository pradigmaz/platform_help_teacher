"""Shared submission state transitions for queue/accept/reject flows."""

from datetime import date, datetime
from uuid import UUID

from app.models.lesson import Lesson
from app.models.submission import Submission, SubmissionStatus


def move_submission_to_ready(
    submission: Submission,
    *,
    ready_at: datetime,
    variant_number: int | None,
    lesson: Lesson | None = None,
) -> None:
    """Normalize a submission when student enters the queue again."""
    submission.status = SubmissionStatus.READY
    submission.ready_at = ready_at
    submission.variant_number = variant_number
    submission.grade = None
    submission.accepted_at = None
    if lesson is not None:
        submission.lesson_id = lesson.id
        submission.lesson_date = lesson.date
        submission.lesson_number = lesson.lesson_number


def move_submission_to_rejected(submission: Submission, *, comment: str) -> None:
    """Normalize a submission when teacher rejects it."""
    submission.status = SubmissionStatus.REJECTED
    submission.feedback = comment
    submission.grade = None
    submission.accepted_at = None
    submission.ready_at = None


def move_submission_to_new(submission: Submission) -> None:
    """Normalize a submission when student leaves the queue."""
    submission.status = SubmissionStatus.NEW
    submission.ready_at = None
    submission.grade = None
    submission.accepted_at = None


def clear_submission_lesson_context(submission: Submission) -> None:
    """Drop stale lesson projection fields when a submission is no longer tied to a slot."""
    submission.lesson_id = None
    submission.lesson_date = None
    submission.lesson_number = None


def move_submission_to_accepted(
    submission: Submission,
    *,
    grade: int,
    comment: str | None,
    accepted_at: datetime,
    lesson_id: UUID | None = None,
    lesson_date: date | None = None,
    lesson_number: int | None = None,
) -> None:
    """Normalize a submission when teacher accepts it."""
    submission.status = SubmissionStatus.ACCEPTED
    submission.grade = grade
    submission.feedback = comment
    submission.accepted_at = accepted_at
    if lesson_id is not None:
        submission.lesson_id = lesson_id
        submission.lesson_date = lesson_date
        submission.lesson_number = lesson_number
