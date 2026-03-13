"""Accepted submission fallbacks for attestation lab scoring."""

from collections import defaultdict
from uuid import UUID

from sqlalchemy import Date, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attestation_settings import AttestationSettings
from app.models.lab import Lab
from app.models.lesson import Lesson
from app.models.schedule import LessonType
from app.models.submission import Submission, SubmissionStatus

from .lab_progress import dedupe_submission_lab_grades


def _build_submission_fallback_query(
    student_filter,
    group_id: UUID,
    settings: AttestationSettings,
    subject_id: UUID | None = None,
):
    period_start, period_end = settings.get_effective_period()
    subject_expr = func.coalesce(Lesson.subject_id, Lab.subject_id)
    period_date_expr = func.coalesce(
        Lesson.date,
        Submission.lesson_date,
        cast(Submission.accepted_at, Date),
        cast(Submission.created_at, Date),
    )

    query = (
        select(Submission, subject_expr, Lab.number)
        .join(Lab, Submission.lab_id == Lab.id)
        .outerjoin(Lesson, Submission.lesson_id == Lesson.id)
        .where(student_filter)
        .where(Submission.status == SubmissionStatus.ACCEPTED)
        .where(Submission.grade.isnot(None))
        .where(Submission.deleted_at.is_(None))
        .where(subject_expr.isnot(None))
        .where(period_date_expr.isnot(None))
        .where(period_date_expr >= period_start)
        .where(period_date_expr <= period_end)
        .where(or_(Submission.lesson_id.is_(None), Lesson.is_cancelled.is_(False)))
        .where(or_(Submission.lesson_id.is_(None), Lesson.lesson_type.in_((LessonType.LAB, LessonType.PRACTICE))))
        .where(or_(Lesson.group_id == group_id, Submission.lesson_id.is_(None)))
    )
    if subject_id is not None:
        query = query.where(subject_expr == subject_id)
    return query


async def get_student_submission_grade_fallbacks(
    db: AsyncSession,
    student_id: UUID,
    group_id: UUID,
    settings: AttestationSettings,
    subject_id: UUID | None = None,
) -> list[dict]:
    """Load accepted submissions that can fill missing journal grades."""
    query = _build_submission_fallback_query(Submission.user_id == student_id, group_id, settings, subject_id)
    result = await db.execute(query)
    return dedupe_submission_lab_grades(result.all())


async def get_submission_grade_fallbacks_batch(
    db: AsyncSession,
    student_ids: list[UUID],
    group_id: UUID,
    settings: AttestationSettings,
    subject_id: UUID | None = None,
) -> dict[UUID, list[dict]]:
    """Batch-load accepted submission fallbacks grouped by student."""
    if not student_ids:
        return {}

    query = _build_submission_fallback_query(Submission.user_id.in_(student_ids), group_id, settings, subject_id)
    result = await db.execute(query)

    rows_by_student: dict[UUID, list[tuple[Submission, UUID | None, int | None]]] = defaultdict(list)
    for submission, row_subject_id, work_number in result.all():
        rows_by_student[submission.user_id].append((submission, row_subject_id, work_number))

    return {student_id: dedupe_submission_lab_grades(rows) for student_id, rows in rows_by_student.items()}
