from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from app.services.rate_limit.admin import get_active_bans, unban_by_warning_id
from app.services.rate_limit.models import RateLimitWarning


@pytest.mark.asyncio
async def test_get_active_bans_enriches_user_name() -> None:
    db = AsyncMock()
    user_id = uuid4()
    warning = RateLimitWarning(
        id=uuid4(),
        user_id=user_id,
        ip_address="127.0.0.1",
        warning_level="soft_ban",
        violation_count=20,
        message="slow down",
        ban_until=datetime.now(UTC) + timedelta(minutes=10),
        unbanned_at=None,
        admin_notified=False,
        created_at=datetime.now(UTC),
    )
    user = type("UserRow", (), {"id": user_id, "full_name": "Admin Student"})()

    warning_result = Mock()
    warning_scalars = Mock()
    warning_scalars.all.return_value = [warning]
    warning_result.scalars.return_value = warning_scalars
    users_result = Mock()
    users_scalars = Mock()
    users_scalars.all.return_value = [user]
    users_result.scalars.return_value = users_scalars

    db.execute.side_effect = [warning_result, users_result]
    db.scalar.return_value = 1

    response = await get_active_bans(db)

    assert response.total == 1
    assert len(response.items) == 1
    assert response.items[0].user_id == user_id
    assert response.items[0].user_name == "Admin Student"


@pytest.mark.asyncio
async def test_unban_by_warning_id_updates_warning_and_clears_redis_keys() -> None:
    db = AsyncMock()
    warning_id = uuid4()
    admin_id = uuid4()
    user_id = uuid4()
    warning = RateLimitWarning(
        id=warning_id,
        user_id=user_id,
        ip_address="10.0.0.1",
        warning_level="hard_ban",
        violation_count=40,
        message="blocked",
        ban_until=datetime.now(UTC) + timedelta(hours=1),
        unbanned_at=None,
        admin_notified=True,
        created_at=datetime.now(UTC),
    )
    db.get.return_value = warning

    redis = AsyncMock()

    with patch("app.services.rate_limit.admin.get_redis", return_value=redis):
        success = await unban_by_warning_id(db, warning_id, admin_id, "manual unban")

    assert success is True
    assert warning.unbanned_by == admin_id
    assert warning.unban_reason == "manual unban"
    assert warning.unbanned_at is not None
    assert warning.unbanned_at.tzinfo is UTC
    db.commit.assert_awaited_once()

    deleted_keys = [call.args[0] for call in redis.delete.await_args_list]
    assert "rl:ban:ip:10.0.0.1" in deleted_keys
    assert f"rl:ban:user:{user_id}" in deleted_keys
    assert "rl:429:ip:10.0.0.1" in deleted_keys
    assert f"rl:429:user:{user_id}" in deleted_keys
