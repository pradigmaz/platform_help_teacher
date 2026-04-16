from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_group_subject_offering import (
    get_current_semester_key,
    get_group_subject_offering,
    list_active_students_for_group,
    list_group_subject_offerings_for_group,
    list_offering_refusals,
)
from app.models.group_subject_offering import FinalControlType, GroupSubjectOffering
from app.models.lab import Lab
from app.models.lesson import Lesson
from app.models.lesson_grade import LessonGrade
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User
from app.services.attestation.lab_progress import is_completed_lab_grade


@dataclass(frozen=True)
class AutomaticQueueEntry:
    student_id: UUID
    student_name: str
    completed_count: int
    automatic_remaining: int
    completion_at: datetime | None
    queue_position: int | None
    is_winner: bool
    is_declined: bool
    declined_reason: str | None


@dataclass(frozen=True)
class AutomaticOfferingResolution:
    offering: GroupSubjectOffering | None
    reason: str | None


def _register_completion(
    completion_map: dict[UUID, dict[int, datetime]],
    *,
    student_id: UUID,
    work_number: int,
    completed_at: datetime | None,
) -> None:
    if completed_at is None:
        return
    student_completions = completion_map[student_id]
    current = student_completions.get(work_number)
    if current is None or completed_at < current:
        student_completions[work_number] = completed_at


def build_automatic_queue_entries(
    *,
    students: list[User],
    completion_map: dict[UUID, dict[int, datetime]],
    total_labs: int,
    automatic_places: int | None,
    declined_by_student_id: dict[UUID, str | None],
) -> list[AutomaticQueueEntry]:
    ranking = sorted(
        (
            max(work_map.values()),
            str(student_id),
            student_id,
        )
        for student_id, work_map in completion_map.items()
        if len(work_map) >= total_labs and student_id not in declined_by_student_id
    )
    ranking_position_by_student = {
        student_id: index
        for index, (_, _, student_id) in enumerate(ranking, start=1)
    }

    entries: list[AutomaticQueueEntry] = []
    for student in students:
        student_completions = completion_map.get(student.id, {})
        completed_count = len(student_completions)
        automatic_remaining = max(total_labs - completed_count, 0)
        completion_at = max(student_completions.values()) if student_completions else None
        queue_position = ranking_position_by_student.get(student.id)
        is_winner = bool(
            queue_position is not None
            and automatic_places is not None
            and automatic_places > 0
            and queue_position <= automatic_places
        )
        entries.append(
            AutomaticQueueEntry(
                student_id=student.id,
                student_name=student.full_name,
                completed_count=completed_count,
                automatic_remaining=automatic_remaining,
                completion_at=completion_at,
                queue_position=queue_position,
                is_winner=is_winner,
                is_declined=student.id in declined_by_student_id,
                declined_reason=declined_by_student_id.get(student.id),
            )
        )

    entries.sort(
        key=lambda entry: (
            entry.is_declined,
            entry.queue_position is None,
            entry.queue_position or 10**6,
            entry.automatic_remaining,
            entry.student_name.lower(),
            str(entry.student_id),
        )
    )
    return entries


async def resolve_student_automatic_offering(
    db: AsyncSession,
    *,
    student: User,
    subject_id: UUID | None,
) -> AutomaticOfferingResolution:
    if student.group_id is None:
        return AutomaticOfferingResolution(offering=None, reason="group_missing")

    semester_key = await get_current_semester_key(db)
    if subject_id is not None:
        offering = await get_group_subject_offering(
            db,
            group_id=student.group_id,
            subject_id=subject_id,
            semester=semester_key,
        )
        if offering is None:
            return AutomaticOfferingResolution(offering=None, reason="offering_missing")
        return AutomaticOfferingResolution(offering=offering, reason=None)

    offerings = await list_group_subject_offerings_for_group(
        db,
        group_id=student.group_id,
        semester=semester_key,
    )
    if len(offerings) == 1:
        return AutomaticOfferingResolution(offering=offerings[0], reason=None)
    if len(offerings) > 1:
        return AutomaticOfferingResolution(offering=None, reason="subject_required")
    return AutomaticOfferingResolution(offering=None, reason="offering_missing")


async def load_completion_map(
    db: AsyncSession,
    *,
    student_ids: list[UUID],
    subject_id: UUID,
    total_labs: int,
) -> dict[UUID, dict[int, datetime]]:
    completion_map: dict[UUID, dict[int, datetime]] = defaultdict(dict)

    lesson_grades_result = await db.execute(
        select(LessonGrade.student_id, LessonGrade.work_number, LessonGrade.updated_at, LessonGrade.created_at, LessonGrade.grade)
        .join(Lesson, LessonGrade.lesson_id == Lesson.id)
        .where(LessonGrade.student_id.in_(student_ids))
        .where(LessonGrade.work_number.is_not(None))
        .where(LessonGrade.work_number >= 1)
        .where(LessonGrade.work_number <= total_labs)
        .where(Lesson.subject_id == subject_id)
        .where(Lesson.is_cancelled.is_(False))
    )
    for student_id, work_number, updated_at, created_at, grade in lesson_grades_result.all():
        if work_number is None or not is_completed_lab_grade(grade):
            continue
        _register_completion(
            completion_map,
            student_id=student_id,
            work_number=work_number,
            completed_at=updated_at or created_at,
        )

    submission_result = await db.execute(
        select(Submission.user_id, Lab.number, Submission.accepted_at, Submission.updated_at, Submission.created_at)
        .join(Lab, Submission.lab_id == Lab.id)
        .where(Submission.user_id.in_(student_ids))
        .where(Submission.status == SubmissionStatus.ACCEPTED)
        .where(Lab.subject_id == subject_id)
        .where(Lab.deleted_at.is_(None))
        .where(Lab.number >= 1)
        .where(Lab.number <= total_labs)
    )
    for student_id, work_number, accepted_at, updated_at, created_at in submission_result.all():
        _register_completion(
            completion_map,
            student_id=student_id,
            work_number=work_number,
            completed_at=accepted_at or updated_at or created_at,
        )

    return completion_map


async def list_offering_automatic_queue(
    db: AsyncSession,
    *,
    offering: GroupSubjectOffering,
    total_labs: int,
    automatic_places: int | None,
) -> list[AutomaticQueueEntry]:
    students = await list_active_students_for_group(db, group_id=offering.group_id)
    if not students:
        return []

    completion_map = await load_completion_map(
        db,
        student_ids=[student.id for student in students],
        subject_id=offering.subject_id,
        total_labs=total_labs,
    )
    refusals = await list_offering_refusals(db, offering_id=offering.id)
    declined_by_student_id = {refusal.student_id: refusal.reason for refusal in refusals}
    return build_automatic_queue_entries(
        students=students,
        completion_map=completion_map,
        total_labs=total_labs,
        automatic_places=automatic_places,
        declined_by_student_id=declined_by_student_id,
    )


def offering_allows_automatic(offering: GroupSubjectOffering | None) -> bool:
    return offering is not None and offering.final_control_type == FinalControlType.EXAM
