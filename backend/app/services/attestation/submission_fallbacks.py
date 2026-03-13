"""Accepted submission fallbacks for attestation lab scoring."""

from collections import defaultdict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attestation_settings import AttestationSettings
from app.models.lab import Lab
from app.models.lesson import Lesson
from app.models.submission import Submission, SubmissionStatus

from .lab_progress import dedupe_submission_lab_grades


async def get_student_submission_grade_fallbacks(
    db: AsyncSession,
    student_id: UUID,
    group_id: UUID,
    settings: AttestationSettings,
) -> list[dict]:
    """Load accepted submissions that can fill missing journal grades."""
    period_start, period_end = settings.get_effective_period()
    query = (
        select(Submission, Lesson.subject_id, Lab.number)
        .join(Lab, Submission.lab_id == Lab.id)
        .join(Lesson, Submission.lesson_id == Lesson.id)
        .where(Submission.user_id == student_id)
        .where(Submission.status == SubmissionStatus.ACCEPTED)
        .where(Submission.grade.isnot(None))
        .where(Submission.deleted_at.is_(None))
        .where(Submission.lesson_id.isnot(None))
        .where(Lesson.subject_id.isnot(None))
        .where(Lesson.group_id == group_id)
        .where(Lesson.is_cancelled.is_(False))
        .where(Lesson.date >= period_start)
        .where(Lesson.date <= period_end)
    )
    result = await db.execute(query)
    return dedupe_submission_lab_grades(result.all())


async def get_submission_grade_fallbacks_batch(
    db: AsyncSession,
    student_ids: list[UUID],
    group_id: UUID,
    settings: AttestationSettings,
) -> dict[UUID, list[dict]]:
    """Batch-load accepted submission fallbacks grouped by student."""
    if not student_ids:
        return {}

    period_start, period_end = settings.get_effective_period()
    query = (
        select(Submission, Lesson.subject_id, Lab.number)
        .join(Lab, Submission.lab_id == Lab.id)
        .join(Lesson, Submission.lesson_id == Lesson.id)
        .where(Submission.user_id.in_(student_ids))
        .where(Submission.status == SubmissionStatus.ACCEPTED)
        .where(Submission.grade.isnot(None))
        .where(Submission.deleted_at.is_(None))
        .where(Submission.lesson_id.isnot(None))
        .where(Lesson.subject_id.isnot(None))
        .where(Lesson.group_id == group_id)
        .where(Lesson.is_cancelled.is_(False))
        .where(Lesson.date >= period_start)
        .where(Lesson.date <= period_end)
    )
    result = await db.execute(query)

    rows_by_student: dict[UUID, list[tuple[Submission, UUID | None, int | None]]] = defaultdict(list)
    for submission, subject_id, work_number in result.all():
        rows_by_student[submission.user_id].append((submission, subject_id, work_number))

    return {student_id: dedupe_submission_lab_grades(rows) for student_id, rows in rows_by_student.items()}
