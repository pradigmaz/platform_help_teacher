from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.services.attestation.automatic_queue import _get_offering_date_range, list_offering_automatic_queue


def test_offering_date_range_matches_semester_key_boundaries():
    first_start, first_end = _get_offering_date_range("2025-1")
    second_start, second_end = _get_offering_date_range("2026-2")

    assert first_start.isoformat() == "2025-09-01"
    assert first_end.isoformat() == "2026-01-31"
    assert second_start.isoformat() == "2026-02-01"
    assert second_end.isoformat() == "2026-08-31"


@pytest.mark.asyncio
async def test_offering_automatic_queue_passes_concrete_offering_scope_to_completion_loader():
    student_id = uuid4()
    offering = SimpleNamespace(
        id=uuid4(),
        group_id=uuid4(),
        subject_id=uuid4(),
        semester="2026-2",
    )
    student = SimpleNamespace(id=student_id, full_name="Студент Тестов")
    db = AsyncMock()

    with (
        patch(
            "app.services.attestation.automatic_queue.list_active_students_for_group",
            new=AsyncMock(return_value=[student]),
        ),
        patch(
            "app.services.attestation.automatic_queue.list_offering_refusals",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "app.services.attestation.automatic_queue.load_completion_map",
            new=AsyncMock(return_value={student_id: {1: datetime(2026, 2, 10), 2: datetime(2026, 2, 12)}}),
        ) as load_completion_map,
    ):
        await list_offering_automatic_queue(
            db,
            offering=offering,
            total_labs=2,
            automatic_places=1,
        )

    load_completion_map.assert_awaited_once_with(
        db,
        student_ids=[student_id],
        group_id=offering.group_id,
        subject_id=offering.subject_id,
        offering_id=offering.id,
        semester=offering.semester,
        total_labs=2,
    )
