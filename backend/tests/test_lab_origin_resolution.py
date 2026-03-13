from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.lab import Lab
from app.models.lesson import Lesson
from app.models.schedule import LessonType
from app.services.attestation.deadline_validator import get_max_allowed_grade_for_lab
from app.services.attestation.lab_slot_validator import (
    get_unsubmitted_excused_labs_count,
    is_excused_lab,
)


@pytest.mark.asyncio
async def test_deadline_validator_uses_current_group_origin_lesson(monkeypatch):
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: None))
    db.get = AsyncMock(side_effect=AssertionError("global lab.lesson_id must not be used here"))

    subject_id = uuid4()
    current_lesson = Lesson(
        id=uuid4(),
        group_id=uuid4(),
        subject_id=subject_id,
        date=date(2026, 3, 13),
        lesson_number=2,
        lesson_type=LessonType.LAB,
    )
    origin_lesson = Lesson(
        id=uuid4(),
        group_id=current_lesson.group_id,
        subject_id=subject_id,
        date=date(2026, 2, 20),
        lesson_number=1,
        lesson_type=LessonType.LAB,
    )
    lab = Lab(
        id=uuid4(),
        number=4,
        subject_id=subject_id,
        lesson_id=uuid4(),
        deadline_5_lessons=1,
        deadline_4_lessons=2,
    )

    resolve_origin = AsyncMock(return_value=origin_lesson)
    monkeypatch.setattr(
        "app.services.attestation.deadline_validator._get_origin_lesson_for_group",
        resolve_origin,
    )
    monkeypatch.setattr(
        "app.services.attestation.deadline_validator._get_extension_bonus",
        AsyncMock(return_value=0),
    )
    monkeypatch.setattr(
        "app.services.attestation.deadline_validator._get_lesson_index",
        AsyncMock(return_value=2),
    )

    result = await get_max_allowed_grade_for_lab(db, lab, current_lesson, student_id=uuid4())

    assert result == 4
    resolve_origin.assert_awaited_once_with(db, current_lesson, lab.number)
    db.get.assert_not_called()


@pytest.mark.asyncio
async def test_unsubmitted_excused_labs_count_uses_excused_work_numbers():
    db = AsyncMock()
    db.execute = AsyncMock(
        side_effect=[
            MagicMock(fetchall=lambda: [(3,), (4,)]),
            MagicMock(scalar=lambda: 1),
        ]
    )

    result = await get_unsubmitted_excused_labs_count(db, uuid4(), uuid4())

    assert result == 1


@pytest.mark.asyncio
async def test_is_excused_lab_checks_subject_and_work_number_not_global_lesson_id():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: object()))
    lab = Lab(id=uuid4(), number=3, subject_id=uuid4(), lesson_id=uuid4())

    result = await is_excused_lab(db, uuid4(), lab)

    assert result is True
    db.execute.assert_awaited_once()
