from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.lab import Lab
from app.models.lesson import Lesson
from app.schemas.lab import LabUpdate
from app.services.lab_service import LabService


@pytest.mark.asyncio
async def test_update_number_reassigns_attached_lessons_and_resyncs_origin_lesson():
    service = LabService()
    subject_id = uuid4()
    new_origin = Lesson(id=uuid4(), subject_id=subject_id, work_number=4)

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(
        side_effect=[
            MagicMock(rowcount=2),
            MagicMock(scalar_one_or_none=lambda: new_origin),
        ]
    )
    mock_db.get = AsyncMock(return_value=Lesson(id=uuid4(), subject_id=subject_id))

    lab = Lab(
        id=uuid4(),
        number=3,
        subject_id=subject_id,
        lesson_id=uuid4(),
        title="Lab 3",
    )

    result = await service.update(mock_db, lab, LabUpdate(number=4))

    assert result.number == 4
    assert result.lesson_id == new_origin.id
    assert mock_db.execute.await_count == 2

    update_query = str(mock_db.execute.await_args_list[0].args[0]).lower()
    origin_query = str(mock_db.execute.await_args_list[1].args[0]).lower()

    assert "update lessons" in update_query
    assert "work_number" in update_query
    assert "select lessons.id" in origin_query or "from lessons" in origin_query
