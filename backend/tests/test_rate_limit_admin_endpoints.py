from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.admin_rate_limit import (
    list_active_bans,
    list_warnings_history,
    unban_user,
    unban_warning,
)
from app.services.rate_limit.schemas import UnbanRequest, WarningListResponse, WarningRecord


@pytest.mark.asyncio
async def test_list_active_bans_endpoint_returns_service_payload() -> None:
    db = AsyncMock()
    payload = WarningListResponse(
        items=[
            WarningRecord(
                id=uuid4(),
                user_id=None,
                user_name=None,
                ip_address="127.0.0.1",
                warning_level="soft_ban",
                violation_count=20,
                message="slow down",
                ban_until=datetime.now(UTC) + timedelta(minutes=10),
                unbanned_at=None,
                admin_notified=False,
                created_at=datetime.now(UTC),
            )
        ],
        total=1,
    )

    with patch("app.api.v1.endpoints.admin_rate_limit.get_active_bans", new=AsyncMock(return_value=payload)) as mock_get:
        response = await list_active_bans(db=db, _=Mock(), skip=5, limit=10)

    assert response == payload
    mock_get.assert_awaited_once_with(db, 5, 10)


@pytest.mark.asyncio
async def test_list_warnings_history_endpoint_passes_filters() -> None:
    db = AsyncMock()
    user_id = uuid4()
    payload = WarningListResponse(items=[], total=0)

    with patch(
        "app.api.v1.endpoints.admin_rate_limit.get_warnings_history",
        new=AsyncMock(return_value=payload),
    ) as mock_get:
        response = await list_warnings_history(
            db=db,
            _=Mock(),
            user_id=user_id,
            ip_address="127.0.0.1",
            skip=3,
            limit=7,
        )

    assert response == payload
    mock_get.assert_awaited_once_with(db, user_id, "127.0.0.1", 3, 7)


@pytest.mark.asyncio
async def test_unban_warning_endpoint_returns_404_when_warning_is_missing() -> None:
    warning_id = uuid4()

    with (
        patch("app.api.v1.endpoints.admin_rate_limit.unban_by_warning_id", new=AsyncMock(return_value=False)),
        pytest.raises(HTTPException) as exc_info,
    ):
        await unban_warning(
            warning_id=warning_id,
            request=UnbanRequest(reason="manual"),
            db=AsyncMock(),
            admin=type("Admin", (), {"id": uuid4()})(),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Warning not found"


@pytest.mark.asyncio
async def test_unban_warning_endpoint_returns_success_payload() -> None:
    warning_id = uuid4()
    admin = type("Admin", (), {"id": uuid4()})()
    db = AsyncMock()

    with patch("app.api.v1.endpoints.admin_rate_limit.unban_by_warning_id", new=AsyncMock(return_value=True)) as mock_unban:
        response = await unban_warning(
            warning_id=warning_id,
            request=UnbanRequest(reason="manual"),
            db=db,
            admin=admin,
        )

    assert response.success is True
    assert response.message == "Пользователь разбанен"
    assert response.warning_id == warning_id
    mock_unban.assert_awaited_once_with(db, warning_id, admin.id, "manual")


@pytest.mark.asyncio
async def test_unban_user_endpoint_returns_count_message() -> None:
    user_id = uuid4()
    admin = type("Admin", (), {"id": uuid4()})()
    db = AsyncMock()

    with patch("app.api.v1.endpoints.admin_rate_limit.unban_by_user_id", new=AsyncMock(return_value=2)) as mock_unban:
        response = await unban_user(
            user_id=user_id,
            request=UnbanRequest(reason="manual"),
            db=db,
            admin=admin,
        )

    assert response.success is True
    assert response.message == "Снято 2 банов"
    assert response.warning_id == user_id
    mock_unban.assert_awaited_once_with(db, user_id, admin.id, "manual")
