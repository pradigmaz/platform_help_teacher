from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.api.v1.endpoints.admin_lab_schedule import get_schedule_slots
from app.models.lab import Lab
from app.models.lesson import Lesson
from app.models.schedule import LessonType


@pytest.mark.asyncio
async def test_get_schedule_slots_sets_attachment_block_per_group_only(monkeypatch):
    lab = Lab(id=uuid4(), number=2, subject_id=uuid4(), title="Lab 2")

    first_group_id = uuid4()
    second_group_id = uuid4()
    lessons = [
        Lesson(
            id=uuid4(),
            group_id=first_group_id,
            subject_id=lab.subject_id,
            date=date(2026, 3, 10),
            lesson_number=1,
            lesson_type=LessonType.LAB,
            group=SimpleNamespace(name="A"),
        ),
        Lesson(
            id=uuid4(),
            group_id=second_group_id,
            subject_id=lab.subject_id,
            date=date(2026, 3, 10),
            lesson_number=1,
            lesson_type=LessonType.LAB,
            group=SimpleNamespace(name="B"),
        ),
    ]

    mock_db = AsyncMock()
    mock_db.get = AsyncMock(return_value=lab)
    mock_db.execute = AsyncMock(
        return_value=MagicMock(
            scalars=lambda: MagicMock(unique=lambda: MagicMock(all=lambda: lessons))
        )
    )

    async def fake_validate_attachment(self, *, lab_to_attach, target_lesson_date, group_id, subject_id):
        if group_id == first_group_id:
            return SimpleNamespace(
                is_valid=False,
                blocking_lab_number=1,
                can_attach_from=date(2026, 3, 17),
                message="blocked for first group",
            )
        return SimpleNamespace(is_valid=True, blocking_lab_number=None, can_attach_from=None, message="")

    monkeypatch.setattr(
        "app.api.v1.endpoints.admin_lab_schedule.LabAttachmentValidator.validate_attachment",
        fake_validate_attachment,
    )

    result = await get_schedule_slots(lab.id, db=mock_db, _=SimpleNamespace())

    groups = {group.group_name: group for group in result.groups}
    assert groups["A"].attachment_blocked is not None
    assert groups["B"].attachment_blocked is None
    assert result.attachment_blocked is None
