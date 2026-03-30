from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from app.services.rate_limit.admin import (
    get_active_bans,
    get_warnings_history,
    unban_by_user_id,
    unban_by_warning_id,
)
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

    warning_result = Mock()
    warning_scalars = Mock()
    warning_scalars.all.return_value = [warning]
    warning_result.scalars.return_value = warning_scalars

    user_rows = Mock()
    user_row = type("UserRow", (), {"id": user_id, "full_name": "Admin Student"})()
    user_rows.all.return_value = [user_row]

    db.execute.side_effect = [warning_result, user_rows]
    db.scalar.return_value = 1

    response = await get_active_bans(db)

    assert response.total == 1
    assert len(response.items) == 1
    assert response.items[0].user_id == user_id
    assert response.items[0].user_name == "Admin Student"


@pytest.mark.asyncio
async def test_get_active_bans_queries_only_active_not_unbanned_records() -> None:
    db = AsyncMock()
    warning_result = Mock()
    warning_scalars = Mock()
    warning_scalars.all.return_value = []
    warning_result.scalars.return_value = warning_scalars
    db.execute.return_value = warning_result
    db.scalar.return_value = 0

    response = await get_active_bans(db)

    assert response.total == 0
    assert response.items == []

    query_sql = str(db.execute.await_args.args[0]).lower()
    count_sql = str(db.scalar.await_args.args[0]).lower()

    assert "ban_until is not null" in query_sql
    assert "ban_until >" in query_sql
    assert "unbanned_at is null" in query_sql
    assert "ban_until is not null" in count_sql
    assert "ban_until >" in count_sql
    assert "unbanned_at is null" in count_sql


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

    with patch("app.services.rate_limit.admin_redis.get_redis", return_value=redis):
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


@pytest.mark.asyncio
async def test_get_warnings_history_applies_user_and_ip_filters() -> None:
    db = AsyncMock()
    user_id = uuid4()
    warning = RateLimitWarning(
        id=uuid4(),
        user_id=user_id,
        ip_address="10.10.10.10",
        warning_level="soft_warning",
        violation_count=15,
        message="tracked",
        ban_until=None,
        unbanned_at=None,
        admin_notified=False,
        created_at=datetime.now(UTC),
    )

    warning_result = Mock()
    warning_scalars = Mock()
    warning_scalars.all.return_value = [warning]
    warning_result.scalars.return_value = warning_scalars

    user_rows = Mock()
    user_row = type("UserRow", (), {"id": user_id, "full_name": "History User"})()
    user_rows.all.return_value = [user_row]

    db.execute.side_effect = [warning_result, user_rows]
    db.scalar.return_value = 1

    response = await get_warnings_history(db, user_id=user_id, ip_address="10.10.10.10")

    assert response.total == 1
    assert response.items[0].user_name == "History User"

    query_sql = str(db.execute.await_args_list[0].args[0]).lower()
    count_sql = str(db.scalar.await_args.args[0]).lower()

    assert "user_id" in query_sql
    assert "ip_address" in query_sql
    assert "user_id" in count_sql
    assert "ip_address" in count_sql


@pytest.mark.asyncio
async def test_unban_by_user_id_updates_all_active_warnings_and_clears_user_keys() -> None:
    db = AsyncMock()
    user_id = uuid4()
    admin_id = uuid4()
    warnings = [
        RateLimitWarning(
            id=uuid4(),
            user_id=user_id,
            ip_address="10.0.0.1",
            warning_level="soft_ban",
            violation_count=20,
            message="first",
            ban_until=datetime.now(UTC) + timedelta(minutes=10),
            unbanned_at=None,
            admin_notified=False,
            created_at=datetime.now(UTC),
        ),
        RateLimitWarning(
            id=uuid4(),
            user_id=user_id,
            ip_address="10.0.0.2",
            warning_level="hard_ban",
            violation_count=40,
            message="second",
            ban_until=datetime.now(UTC) + timedelta(hours=1),
            unbanned_at=None,
            admin_notified=True,
            created_at=datetime.now(UTC),
        ),
    ]

    result = Mock()
    scalars = Mock()
    scalars.all.return_value = warnings
    result.scalars.return_value = scalars
    db.execute.return_value = result

    redis = AsyncMock()

    with patch("app.services.rate_limit.admin_redis.get_redis", return_value=redis):
        count = await unban_by_user_id(db, user_id, admin_id, "batch unban")

    assert count == 2
    db.commit.assert_awaited_once()

    for warning in warnings:
        assert warning.unbanned_by == admin_id
        assert warning.unban_reason == "batch unban"
        assert warning.unbanned_at is not None
        assert warning.unbanned_at.tzinfo is UTC

    deleted_keys = [call.args[0] for call in redis.delete.await_args_list]
    assert deleted_keys == [f"rl:ban:user:{user_id}", f"rl:429:user:{user_id}"]
