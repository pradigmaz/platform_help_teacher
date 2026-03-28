from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.lab import Lab
from app.services.lab_lookup import find_active_lab_by_subject_and_number, find_active_labs_by_subject_and_numbers


def _result_for(*labs: Lab):
    scalars = MagicMock()
    scalars.all.return_value = list(labs)
    result = MagicMock()
    result.scalars.return_value = scalars
    return result


def _build_lab(*, number: int, subject_id, is_published: bool, created_at: datetime) -> Lab:
    lab = Lab(
        id=uuid4(),
        number=number,
        subject_id=subject_id,
        title=f"Lab {number}",
        is_published=is_published,
        deleted_at=None,
    )
    lab.created_at = created_at
    return lab


@pytest.mark.asyncio
async def test_find_active_lab_prefers_published_candidate_in_legacy_duplicate_set():
    subject_id = uuid4()
    draft_lab = _build_lab(
        number=3,
        subject_id=subject_id,
        is_published=False,
        created_at=datetime(2026, 3, 1, tzinfo=UTC),
    )
    published_lab = _build_lab(
        number=3,
        subject_id=subject_id,
        is_published=True,
        created_at=datetime(2026, 3, 2, tzinfo=UTC),
    )
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=_result_for(draft_lab, published_lab))

    resolved = await find_active_lab_by_subject_and_number(mock_db, subject_id, 3)

    assert resolved == published_lab


@pytest.mark.asyncio
async def test_find_active_lab_returns_none_when_only_unpublished_and_published_required():
    subject_id = uuid4()
    draft_lab = _build_lab(
        number=2,
        subject_id=subject_id,
        is_published=False,
        created_at=datetime(2026, 3, 1, tzinfo=UTC),
    )
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=_result_for(draft_lab))

    resolved = await find_active_lab_by_subject_and_number(mock_db, subject_id, 2, published_only=True)

    assert resolved is None


@pytest.mark.asyncio
async def test_find_active_labs_builds_number_map_with_one_candidate_per_number():
    subject_id = uuid4()
    published_two = _build_lab(
        number=2,
        subject_id=subject_id,
        is_published=True,
        created_at=datetime(2026, 3, 2, tzinfo=UTC),
    )
    draft_two = _build_lab(
        number=2,
        subject_id=subject_id,
        is_published=False,
        created_at=datetime(2026, 3, 1, tzinfo=UTC),
    )
    published_three = _build_lab(
        number=3,
        subject_id=subject_id,
        is_published=True,
        created_at=datetime(2026, 3, 3, tzinfo=UTC),
    )
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=_result_for(draft_two, published_two, published_three))

    resolved = await find_active_labs_by_subject_and_numbers(mock_db, subject_id, {2, 3})

    assert resolved == {2: published_two, 3: published_three}
