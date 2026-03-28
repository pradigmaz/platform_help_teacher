from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models import Lab, Lesson, Submission, User
from app.models.schedule import LessonType
from app.models.submission import SubmissionStatus
from app.models.user import UserRole
from app.services.submission_journal_sync import journal_sync
from app.services.submission_service import submission_service


def _lesson_result(*lessons: Lesson):
    scalars = MagicMock()
    scalars.all.return_value = list(lessons)
    result = MagicMock()
    result.scalars.return_value = scalars
    return result


@pytest.mark.asyncio
async def test_resolve_acceptance_context_prefers_student_subgroup_for_legacy_submission(monkeypatch):
    subject_id = uuid4()
    group_id = uuid4()
    student = User(id=uuid4(), role=UserRole.STUDENT, group_id=group_id, subgroup=2, is_active=True)
    lab = Lab(id=uuid4(), number=3, subject_id=subject_id, title="Lab 3", is_published=True)
    common_lesson = Lesson(
        id=uuid4(),
        subject_id=subject_id,
        group_id=group_id,
        subgroup=None,
        date=date(2026, 3, 20),
        lesson_number=2,
        lesson_type=LessonType.LAB,
        is_cancelled=False,
    )
    subgroup_lesson = Lesson(
        id=uuid4(),
        subject_id=subject_id,
        group_id=group_id,
        subgroup=2,
        date=date(2026, 3, 20),
        lesson_number=2,
        lesson_type=LessonType.LAB,
        is_cancelled=False,
    )
    submission = Submission(
        id=uuid4(),
        user_id=student.id,
        lab_id=lab.id,
        status=SubmissionStatus.READY,
        lesson_date=date(2026, 3, 20),
        lesson_number=2,
    )
    submission.user = student
    submission.lab = lab

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=_lesson_result(common_lesson, subgroup_lesson))
    mock_db.get = AsyncMock()

    fallback_mock = AsyncMock(side_effect=AssertionError("latest-lesson fallback must not be used"))
    monkeypatch.setattr("app.services.submission_service.find_latest_lesson_for_student", fallback_mock)

    _, resolved_lesson = await submission_service.resolve_acceptance_context(mock_db, submission)

    assert resolved_lesson == subgroup_lesson
    fallback_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_resolve_acceptance_context_ignores_cancelled_stored_lesson(monkeypatch):
    subject_id = uuid4()
    group_id = uuid4()
    student = User(id=uuid4(), role=UserRole.STUDENT, group_id=group_id, subgroup=1, is_active=True)
    lab = Lab(id=uuid4(), number=5, subject_id=subject_id, title="Lab 5", is_published=True)
    cancelled_lesson = Lesson(
        id=uuid4(),
        subject_id=subject_id,
        group_id=group_id,
        subgroup=1,
        date=date(2026, 3, 10),
        lesson_number=1,
        lesson_type=LessonType.LAB,
        is_cancelled=True,
    )
    fallback_lesson = Lesson(
        id=uuid4(),
        subject_id=subject_id,
        group_id=group_id,
        subgroup=1,
        date=date(2026, 3, 17),
        lesson_number=2,
        lesson_type=LessonType.PRACTICE,
        is_cancelled=False,
    )
    submission = Submission(
        id=uuid4(),
        user_id=student.id,
        lab_id=lab.id,
        status=SubmissionStatus.READY,
        lesson_id=cancelled_lesson.id,
    )
    submission.user = student
    submission.lab = lab

    mock_db = AsyncMock()
    mock_db.get = AsyncMock(side_effect=[cancelled_lesson])
    mock_db.execute = AsyncMock()

    fallback_mock = AsyncMock(return_value=fallback_lesson)
    monkeypatch.setattr("app.services.submission_service.find_latest_lesson_for_student", fallback_mock)

    _, resolved_lesson = await submission_service.resolve_acceptance_context(mock_db, submission)

    assert resolved_lesson == fallback_lesson
    fallback_mock.assert_awaited_once_with(mock_db, student=student, subject_id=subject_id)


@pytest.mark.asyncio
async def test_find_lesson_for_student_prefers_subgroup_specific_lesson():
    subject_id = uuid4()
    group_id = uuid4()
    student = User(id=uuid4(), role=UserRole.STUDENT, group_id=group_id, subgroup=2, is_active=True)
    common_lesson = Lesson(
        id=uuid4(),
        subject_id=subject_id,
        group_id=group_id,
        subgroup=None,
        date=date(2026, 3, 24),
        lesson_number=3,
        lesson_type=LessonType.LAB,
        is_cancelled=False,
    )
    subgroup_lesson = Lesson(
        id=uuid4(),
        subject_id=subject_id,
        group_id=group_id,
        subgroup=2,
        date=date(2026, 3, 24),
        lesson_number=3,
        lesson_type=LessonType.LAB,
        is_cancelled=False,
    )
    lab = Lab(id=uuid4(), number=7, subject_id=subject_id, title="Lab 7", is_published=True)

    mock_db = AsyncMock()
    mock_db.get = AsyncMock(return_value=student)
    mock_db.execute = AsyncMock(return_value=_lesson_result(common_lesson, subgroup_lesson))

    resolved_lesson = await journal_sync.find_lesson_for_student(mock_db, lab, student.id)

    assert resolved_lesson == subgroup_lesson
