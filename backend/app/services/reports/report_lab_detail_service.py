"""Normalized lab submission slots for public student reports."""

from datetime import UTC, datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lab import Lab
from app.models.submission import Submission, SubmissionStatus
from app.schemas.report import LabSubmission
from app.services.lab_progress_read_model import normalize_lab_progress

from .report_lab_service import (
    _load_lab_catalog_by_number,
    _load_student_journal_grades,
    _resolve_subject_id,
)


def _rank_submission(submission: Submission, subject_match: bool) -> tuple[int, str, str]:
    created_at = (
        submission.accepted_at or submission.ready_at or submission.created_at or datetime.min.replace(tzinfo=UTC)
    )
    return (int(subject_match), created_at.isoformat(), str(submission.id))


def _fallback_lab_id(group_id: UUID, subject_id: UUID | None, work_number: int) -> UUID:
    return uuid5(NAMESPACE_URL, f"report-lab:{group_id}:{subject_id}:{work_number}")


async def _load_student_submissions_by_work(
    db: AsyncSession,
    student_id: UUID,
    total_labs: int,
    subject_id: UUID | None,
) -> dict[int, Submission]:
    query = (
        select(Submission, Lab.number, Lab.subject_id)
        .join(Lab, Submission.lab_id == Lab.id)
        .where(Submission.user_id == student_id)
        .where(Lab.deleted_at.is_(None))
        .where(Lab.number >= 1)
        .where(Lab.number <= total_labs)
    )
    result = await db.execute(query)
    ranked: dict[int, tuple[Submission, bool]] = {}
    for submission, work_number, lab_subject_id in result.all():
        subject_match = subject_id is not None and lab_subject_id == subject_id
        current = ranked.get(work_number)
        if current is None or _rank_submission(submission, subject_match) > _rank_submission(current[0], current[1]):
            ranked[work_number] = (submission, subject_match)
    return {work_number: submission for work_number, (submission, _) in ranked.items()}


async def get_student_lab_submissions(
    db: AsyncSession,
    group_id: UUID,
    student_id: UUID,
    settings,
    subject_id: UUID | None = None,
) -> list[LabSubmission]:
    total_labs = settings.get_labs_count()
    resolved, subject_id = await _resolve_subject_id(db, group_id, settings, subject_id)
    catalog_by_number = await _load_lab_catalog_by_number(db, total_labs, subject_id)
    journal_grades = (
        await _load_student_journal_grades(db, group_id, student_id, settings, subject_id) if resolved else {}
    )
    submissions_by_work = (
        await _load_student_submissions_by_work(db, student_id, total_labs, subject_id) if resolved else {}
    )

    result: list[LabSubmission] = []
    for work_number in range(1, total_labs + 1):
        lab = catalog_by_number.get(work_number)
        submission = submissions_by_work.get(work_number)
        journal_grade = journal_grades.get(work_number)
        progress = normalize_lab_progress(submission, journal_grade)
        result.append(
            LabSubmission(
                lab_id=lab.id if lab else _fallback_lab_id(group_id, subject_id, work_number),
                lab_name=lab.title if lab else f"Лабораторная {work_number}",
                lab_number=work_number,
                grade=float(progress.grade) if progress.grade is not None else None,
                max_grade=float(lab.max_grade if lab else 5),
                submitted_at=progress.submitted_at,
                is_submitted=progress.normalized_status == SubmissionStatus.ACCEPTED.value,
                is_late=False,
            )
        )
    return result
