from datetime import date
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.services.schedule_offering_resolution import (
    ResolvedOfferingScope,
    combine_resolved_scopes,
    resolve_schedule_offering_scope,
)


@pytest.mark.asyncio
async def test_resolve_scope_uses_existing_offering_for_subject_and_date():
    group_id = uuid4()
    subject_id = uuid4()
    offering = type("Offering", (), {"id": uuid4(), "group_id": group_id, "subject_id": subject_id})()
    db = AsyncMock()

    with patch(
        "app.services.schedule_offering_resolution.get_group_subject_offering_for_date",
        new=AsyncMock(return_value=offering),
    ):
        scope = await resolve_schedule_offering_scope(
            db,
            group_id=group_id,
            reference_date=date(2026, 3, 1),
            subject_id=subject_id,
            require_existing=True,
        )

    assert scope == ResolvedOfferingScope(subject_id=subject_id, offering_id=offering.id)


@pytest.mark.asyncio
async def test_resolve_scope_requires_existing_offering_for_manual_subject_binding():
    db = AsyncMock()

    with (
        patch(
            "app.services.schedule_offering_resolution.get_group_subject_offering_for_date",
            new=AsyncMock(return_value=None),
        ),
        pytest.raises(ValueError, match="не найдено семестровое назначение"),
    ):
        await resolve_schedule_offering_scope(
            db,
            group_id=uuid4(),
            reference_date=date(2026, 3, 1),
            subject_id=uuid4(),
            require_existing=True,
        )


def test_combine_resolved_scopes_rejects_subject_conflict():
    with pytest.raises(ValueError, match="не совпадает с элементом расписания"):
        combine_resolved_scopes(
            ResolvedOfferingScope(subject_id=uuid4(), offering_id=None),
            ResolvedOfferingScope(subject_id=uuid4(), offering_id=None),
        )
