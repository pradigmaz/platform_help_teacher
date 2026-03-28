from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.api.v1.endpoints.admin_lab_queue import get_submission_detail
from app.models import Group, Lab, Submission, User
from app.models.submission import SubmissionStatus
from app.models.user import UserRole
from app.services.deadline_trace import DeadlineTrace


def _submission_result(submission: Submission):
    result = MagicMock()
    result.scalar_one_or_none.return_value = submission
    return result


def _build_submission() -> Submission:
    group = Group(id=uuid4(), name="ИТ-11", code="IT11")
    student = User(
        id=uuid4(),
        full_name="Иванов Иван Иванович",
        role=UserRole.STUDENT,
        group_id=group.id,
        subgroup=2,
        is_active=True,
    )
    student.group = group

    lab = Lab(
        id=uuid4(),
        number=3,
        title="Lab 3",
        subject_id=uuid4(),
        deadline_5_lessons=1,
        deadline_4_lessons=2,
        is_published=True,
    )

    submission = Submission(
        id=uuid4(),
        user_id=student.id,
        lab_id=lab.id,
        status=SubmissionStatus.READY,
        ready_at=datetime(2026, 3, 24, 10, 0, tzinfo=UTC),
        variant_number=2,
    )
    submission.user = student
    submission.lab = lab
    return submission


@pytest.mark.asyncio
async def test_submission_detail_exposes_deadline_trace(mock_db, monkeypatch):
    submission = _build_submission()
    trace = DeadlineTrace(
        lesson_index=2,
        current_max_grade=4,
        extension_bonus=1,
        has_extension=True,
        is_excused_origin=False,
        deadline_5_lessons=1,
        deadline_4_lessons=2,
        effective_deadline_5_lessons=2,
        effective_deadline_4_lessons=3,
        deadline_5_status="expired",
        deadline_4_status="active",
        lessons_until_deadline_5=None,
        lessons_until_deadline_4=1,
    )

    mock_db.execute = AsyncMock(return_value=_submission_result(submission))
    monkeypatch.setattr(
        "app.api.v1.endpoints.admin_lab_queue.submission_service.resolve_acceptance_context",
        AsyncMock(return_value=(submission.lab, MagicMock())),
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.admin_lab_queue.get_deadline_trace_for_lab",
        AsyncMock(return_value=trace),
    )

    result = await get_submission_detail(submission.id, db=mock_db, current_user=User(role=UserRole.ADMIN))

    assert result.max_allowed_grade == 4
    assert result.deadline_trace is not None
    assert result.deadline_trace.lesson_index == 2
    assert result.deadline_trace.extension_bonus == 1
    assert result.deadline_trace.effective_deadline_5_lessons == 2
    assert result.deadline_trace.deadline_4_status == "active"


@pytest.mark.asyncio
async def test_submission_detail_keeps_legacy_shape_when_trace_missing(mock_db, monkeypatch):
    submission = _build_submission()

    mock_db.execute = AsyncMock(return_value=_submission_result(submission))
    monkeypatch.setattr(
        "app.api.v1.endpoints.admin_lab_queue.submission_service.resolve_acceptance_context",
        AsyncMock(return_value=(submission.lab, MagicMock())),
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.admin_lab_queue.get_deadline_trace_for_lab",
        AsyncMock(return_value=None),
    )

    result = await get_submission_detail(submission.id, db=mock_db, current_user=User(role=UserRole.ADMIN))

    assert result.max_allowed_grade == 5
    assert result.deadline_trace is None
