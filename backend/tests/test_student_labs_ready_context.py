from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from starlette.requests import Request

from app.api.v1.endpoints.student.labs import mark_lab_ready
from app.models.lab import Lab
from app.models.lesson import Lesson
from app.models.schedule import LessonType
from app.models.user import User, UserRole
from app.services.lab_visibility.models import LabVisibilityInfo


def _build_student(group_id) -> User:
    return User(
        id=uuid4(),
        full_name="Щедрина Анжелина Павловна",
        role=UserRole.STUDENT,
        group_id=group_id,
        subgroup=2,
        is_active=True,
    )


def _build_request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/student/labs/ready",
            "headers": [],
        }
    )


@pytest.mark.asyncio
async def test_mark_lab_ready_passes_current_lesson_context(mock_db, monkeypatch):
    group_id = uuid4()
    subject_id = uuid4()
    lab_id = uuid4()
    student = _build_student(group_id)
    lesson = Lesson(
        id=uuid4(),
        group_id=group_id,
        subject_id=subject_id,
        lesson_number=2,
        lesson_type=LessonType.LAB,
    )
    lab = Lab(
        id=lab_id,
        number=3,
        subject_id=subject_id,
        title="Lab 3",
        deadline_5_lessons=2,
        deadline_4_lessons=4,
        is_published=True,
        deleted_at=None,
    )
    mark_ready_mock = AsyncMock(return_value=SimpleNamespace(id=uuid4()))

    monkeypatch.setattr(
        "app.api.v1.endpoints.student.labs.student_lab_service.get_lab_by_id",
        AsyncMock(return_value=lab),
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.student.labs.LabVisibilityService.get_visibility_info",
        AsyncMock(return_value=LabVisibilityInfo(lab_number=3, is_visible=True)),
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.student.labs.LabVisibilityService.get_current_lab_session",
        AsyncMock(return_value=lesson),
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.student.labs.student_lab_service.check_lab_availability",
        AsyncMock(return_value=True),
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.student.labs.student_lab_service.get_student_position",
        AsyncMock(return_value=1),
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.student.labs.student_lab_service.mark_ready",
        mark_ready_mock,
    )

    await mark_lab_ready(lab_id, _build_request(), db=mock_db, current_user=student)

    assert mark_ready_mock.await_count == 1
    assert mark_ready_mock.await_args.kwargs["lesson"] == lesson
