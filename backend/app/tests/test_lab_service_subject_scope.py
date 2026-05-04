from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.schemas.lab import LabCreate, LabUpdate
from app.services.lab_service import LabService


@pytest.mark.asyncio
async def test_lab_create_requires_subject_after_optional_lesson_sync():
    db = SimpleNamespace(add=Mock(), commit=AsyncMock(), refresh=AsyncMock())

    with pytest.raises(ValueError, match="привязана к предмету"):
        await LabService().create(db, LabCreate(title="Лаба без предмета"))

    db.add.assert_not_called()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_lab_update_rejects_explicit_subject_clear():
    subject_id = uuid4()
    lab = SimpleNamespace(
        id=uuid4(),
        number=1,
        title="Лаба",
        subject_id=subject_id,
        lesson_id=None,
    )
    db = SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock(), execute=AsyncMock())

    with pytest.raises(ValueError, match="привязана к предмету"):
        await LabService().update(db, lab, LabUpdate(subject_id=None))

    assert lab.subject_id == subject_id
    db.commit.assert_not_awaited()
