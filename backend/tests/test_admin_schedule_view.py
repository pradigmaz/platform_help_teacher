from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.v1.endpoints.admin_schedule_view import get_group_students

pytestmark = pytest.mark.smoke


@pytest.mark.asyncio
async def test_get_group_students_includes_subgroup():
    group_id = uuid4()
    student = SimpleNamespace(id=uuid4(), full_name="Иван Иванов", is_active=True, subgroup=2)
    group = SimpleNamespace(users=[student])
    db = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: group)))

    result = await get_group_students(group_id=group_id, db=db, current_user=SimpleNamespace())

    assert result == [{"id": str(student.id), "full_name": "Иван Иванов", "subgroup": 2}]
