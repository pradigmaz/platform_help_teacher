from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models import Lab, Submission
from app.models.lesson import Lesson
from app.models.schedule import LessonType
from app.models.submission import SubmissionStatus
from app.services.student_lab_service import StudentLabService
from app.services.submission_service import SubmissionService


@pytest.mark.asyncio
async def test_mark_ready_clears_stale_acceptance_fields_on_requeue(mock_db):
    service = StudentLabService()
    user_id = uuid4()
    lab_id = uuid4()
    subject_id = uuid4()
    lesson = Lesson(
        id=uuid4(),
        group_id=uuid4(),
        subject_id=subject_id,
        lesson_number=2,
        lesson_type=LessonType.LAB,
    )
    stale_submission = Submission(
        id=uuid4(),
        user_id=user_id,
        lab_id=lab_id,
        status=SubmissionStatus.ACCEPTED,
        is_manual=True,
        grade=5,
        feedback="old accepted comment",
        accepted_at=datetime.now(UTC),
    )
    lab = Lab(id=lab_id, number=3, title="Lab 3", subject_id=subject_id, is_sequential=True)
    rework_grade = MagicMock(grade=2)

    service.get_user_submission_for_lab = AsyncMock(return_value=stale_submission)
    service.get_lab_by_id = AsyncMock(return_value=lab)
    service.get_user_journal_grades_by_subject = AsyncMock(return_value={subject_id: {3: rework_grade}})

    result = await service.mark_ready(mock_db, user_id, lab_id, variant_number=2, lesson=lesson)

    assert result.status == SubmissionStatus.READY
    assert result.grade is None
    assert result.accepted_at is None
    assert result.feedback == "old accepted comment"
    assert result.lesson_id == lesson.id


@pytest.mark.asyncio
async def test_cancel_ready_clears_queue_and_stale_acceptance_fields(mock_db):
    service = StudentLabService()
    user_id = uuid4()
    lab_id = uuid4()
    submission = Submission(
        id=uuid4(),
        user_id=user_id,
        lab_id=lab_id,
        status=SubmissionStatus.READY,
        is_manual=True,
        grade=4,
        feedback="teacher comment",
        ready_at=datetime.now(UTC),
        accepted_at=datetime.now(UTC),
    )

    service.get_user_submission_for_lab = AsyncMock(return_value=submission)

    await service.cancel_ready(mock_db, user_id, lab_id)

    assert submission.status == SubmissionStatus.NEW
    assert submission.ready_at is None
    assert submission.grade is None
    assert submission.accepted_at is None
    assert submission.feedback == "teacher comment"


@pytest.mark.asyncio
async def test_reject_clears_ready_and_grade_fields(mock_db):
    service = SubmissionService()
    submission = Submission(
        id=uuid4(),
        user_id=uuid4(),
        lab_id=uuid4(),
        status=SubmissionStatus.READY,
        is_manual=True,
        grade=5,
        ready_at=datetime.now(UTC),
        accepted_at=datetime.now(UTC),
    )

    result = await service.reject(mock_db, submission, comment="Доработать", rejected_by=uuid4())

    assert result["status"] == "rejected"
    assert submission.status == SubmissionStatus.REJECTED
    assert submission.grade is None
    assert submission.ready_at is None
    assert submission.accepted_at is None
    assert submission.feedback == "Доработать"
