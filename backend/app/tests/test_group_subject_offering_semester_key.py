from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.crud.crud_group_subject_offering import build_semester_key, get_current_semester_key


def test_build_semester_key_uses_semester_year_for_each_term():
    assert build_semester_key(2025, 1) == "2025-1"
    assert build_semester_key(2025, 2) == "2026-2"


@pytest.mark.asyncio
async def test_get_current_semester_key_uses_semester_start_settings():
    db = AsyncMock()

    db.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: None)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.crud.crud_group_subject_offering.today_msk", lambda: date(2026, 4, 20))
        assert await get_current_semester_key(db) == "2026-2"

    db.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: date(2025, 9, 1))
    assert await get_current_semester_key(db) == "2025-1"

    db.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: date(2026, 2, 1))
    assert await get_current_semester_key(db) == "2026-2"
