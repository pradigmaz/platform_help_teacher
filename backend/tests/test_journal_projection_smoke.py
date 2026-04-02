from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models import Lesson, LessonGrade, LessonType, User, UserRole
from app.services.journal_grade_service import JournalGradeWriteService

pytestmark = pytest.mark.smoke


def make_student(*, group_id, subgroup=1) -> User:
    return User(
        id=uuid4(),
        full_name="Smoke Student",
        username="smoke-student",
        role=UserRole.STUDENT,
        group_id=group_id,
        subgroup=subgroup,
        is_active=True,
    )


def make_lesson(*, group_id, subgroup=1) -> Lesson:
    return Lesson(
        id=uuid4(),
        group_id=group_id,
        subject_id=uuid4(),
        date=date(2026, 4, 2),
        lesson_number=1,
        lesson_type=LessonType.LAB,
        work_number=1,
        subgroup=subgroup,
    )


def empty_result():
    result = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = []
    result.scalars.return_value = scalars
    return result


@pytest.mark.asyncio
async def test_upsert_grade_syncs_submission_on_canonical_write(mock_db):
    service = JournalGradeWriteService()
    lesson = make_lesson(group_id=uuid4())
    student = make_student(group_id=lesson.group_id)
    actor_id = uuid4()

    mock_db.get = AsyncMock(return_value=student)
    mock_db.execute = AsyncMock(return_value=empty_result())

    with (
        patch("app.services.journal_grade_service.get_max_allowed_grade", new=AsyncMock(return_value=5)),
        patch("app.services.journal_grade_service.get_student_grade_by_work", new=AsyncMock(return_value=None)),
        patch("app.services.journal_grade_service.journal_sync.sync_from_journal", new=AsyncMock()) as sync_mock,
    ):
        grade = await service.upsert_grade(
            mock_db,
            lesson=lesson,
            student_id=student.id,
            grade=5,
            work_number=1,
            comment="Smoke write",
            actor_id=actor_id,
        )

    assert isinstance(grade, LessonGrade)
    assert grade.lesson_id == lesson.id
    assert grade.student_id == student.id
    assert grade.grade == 5
    assert grade.work_number == 1
    mock_db.add.assert_called_once()
    mock_db.flush.assert_awaited_once()
    sync_mock.assert_awaited_once_with(
        mock_db,
        student_id=student.id,
        lesson=lesson,
        work_number=1,
        grade=5,
        comment="Smoke write",
        created_by=actor_id,
        append_history=True,
    )


@pytest.mark.asyncio
async def test_delete_grade_rolls_submission_projection_back(mock_db):
    service = JournalGradeWriteService()
    lesson = make_lesson(group_id=uuid4())
    grade = LessonGrade(
        lesson_id=lesson.id,
        student_id=uuid4(),
        work_number=1,
        grade=5,
        comment="Smoke write",
        created_by=uuid4(),
    )
    grade.lesson = lesson

    with patch(
        "app.services.journal_grade_service.journal_sync.rollback_from_journal",
        new=AsyncMock(return_value=True),
    ) as rollback_mock:
        await service.delete_grade(mock_db, grade, actor_id=grade.created_by)

    rollback_mock.assert_awaited_once_with(
        mock_db,
        student_id=grade.student_id,
        lesson=lesson,
        work_number=1,
        created_by=grade.created_by,
        append_history=True,
    )
    mock_db.delete.assert_awaited_once_with(grade)
    mock_db.flush.assert_awaited_once()
