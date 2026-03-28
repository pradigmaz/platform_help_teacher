from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.lab import Lab
from app.models.lesson import Lesson
from app.models.schedule import LessonType
from app.services.lab_attachment_validator import LabAttachmentValidator


@pytest.mark.asyncio
async def test_validate_attachment_counts_slots_up_to_target_lesson_date(monkeypatch):
    validator = LabAttachmentValidator(AsyncMock())
    subject_id = uuid4()
    group_id = uuid4()
    target_lesson_date = date(2026, 3, 15)
    first_lesson_date = date(2026, 3, 1)

    prev_lab = Lab(id=uuid4(), number=1, subject_id=subject_id, deadline_5_lessons=2, title="Lab 1")
    next_lab = Lab(id=uuid4(), number=2, subject_id=subject_id, title="Lab 2")

    monkeypatch.setattr(validator, "_get_lab_by_number", AsyncMock(return_value=prev_lab))
    monkeypatch.setattr(
        validator,
        "_get_origin_lesson",
        AsyncMock(return_value=Lesson(id=uuid4(), date=first_lesson_date, lesson_type=LessonType.LAB)),
    )
    count_mock = AsyncMock(return_value=1)
    monkeypatch.setattr(validator, "_count_deadline_slots_from", count_mock)
    monkeypatch.setattr(
        validator,
        "_get_attachment_available_date",
        AsyncMock(return_value=date(2026, 3, 22)),
    )

    result = await validator.validate_attachment(next_lab, target_lesson_date, group_id, subject_id)

    assert result.is_valid is False
    count_mock.assert_awaited_once_with(first_lesson_date, target_lesson_date, group_id, subject_id)


@pytest.mark.asyncio
async def test_attachment_available_date_uses_ordered_slots_including_unnumbered(monkeypatch):
    mock_db = AsyncMock()
    validator = LabAttachmentValidator(mock_db)
    group_id = uuid4()
    subject_id = uuid4()

    monkeypatch.setattr(
        "app.services.lab_attachment_validator.load_ordered_deadline_lessons",
        AsyncMock(
            return_value=[
                (uuid4(), 1, date(2026, 3, 1), 1),
                (uuid4(), None, date(2026, 3, 8), 1),
                (uuid4(), 2, date(2026, 3, 15), 1),
            ]
        ),
    )

    available_date = await validator._get_attachment_available_date(date(2026, 3, 1), 2, group_id, subject_id)

    assert available_date == date(2026, 3, 8)


@pytest.mark.asyncio
async def test_get_lab_by_number_ignores_soft_deleted_labs():
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: None))
    validator = LabAttachmentValidator(mock_db)

    await validator._get_lab_by_number(1, uuid4())

    query = str(mock_db.execute.await_args.args[0]).lower()
    assert "deleted_at is null" in query
