"""Endpoint-level contracts for device read/write behavior."""

import inspect
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest
from starlette.requests import Request as StarletteRequest

from app.api.v1.endpoints import user_devices
from app.models.device import Device


GET_MY_DEVICES = inspect.unwrap(user_devices.get_my_devices)
GET_DEVICE = inspect.unwrap(user_devices.get_device)
UNBIND_DEVICE = inspect.unwrap(user_devices.unbind_device)
CONFIRM_DEVICE = inspect.unwrap(user_devices.confirm_device)
REVOKE_ALL_DEVICES = inspect.unwrap(user_devices.revoke_all_devices)


def make_request(path: str) -> StarletteRequest:
    scope = {"type": "http", "method": "GET", "path": path, "headers": [], "query_string": b""}
    return StarletteRequest(scope)


def make_device(*, user_id, is_trusted=False) -> Device:
    now = datetime.now(UTC)
    return Device(
        id=uuid4(),
        user_id=user_id,
        fingerprint_hash="a" * 64,
        device_info={"platform": "Windows", "browser": "Chrome"},
        first_seen=now,
        last_seen=now,
        is_trusted=is_trusted,
        confirmed_at=None,
        created_at=now,
        updated_at=now,
    )


class TestReadOnlyDeviceEndpoints:
    @pytest.mark.asyncio
    async def test_get_my_devices_does_not_call_commit(self):
        db = AsyncMock()
        user = MagicMock(id=uuid4())
        request = make_request("/me/devices")

        with (
            patch("app.api.v1.endpoints.user_devices.crud_device.get_by_user", AsyncMock(return_value=[])),
            patch("app.api.v1.endpoints.user_devices.crud_device.count_by_user", AsyncMock(return_value=0)),
        ):
            await GET_MY_DEVICES(request=request, current_user=user, db=db)

        db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_device_does_not_call_commit(self):
        db = AsyncMock()
        user = MagicMock(id=uuid4())
        request = make_request("/me/devices/one")
        device = make_device(user_id=user.id)

        with patch("app.api.v1.endpoints.user_devices.crud_device.get_by_id", AsyncMock(return_value=device)):
            await GET_DEVICE(request=request, device_id=uuid4(), current_user=user, db=db)

        db.commit.assert_not_called()


class TestMutatingDeviceEndpoints:
    @pytest.mark.asyncio
    async def test_unbind_device_commits_after_delete(self):
        db = AsyncMock()
        user = MagicMock(id=uuid4())
        request = Mock()
        request.state = Mock()

        with (
            patch("app.api.v1.endpoints.user_devices.crud_device.get_by_id", AsyncMock(return_value=MagicMock(user_id=user.id))),
            patch("app.api.v1.endpoints.user_devices.crud_device.delete_one", AsyncMock(return_value=True)),
        ):
            await UNBIND_DEVICE(request=request, device_id=uuid4(), current_user=user, db=db)

        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_confirm_device_commits_after_update(self):
        db = AsyncMock()
        user = MagicMock(id=uuid4())
        request = Mock()
        request.state = Mock()
        device = make_device(user_id=user.id, is_trusted=False)
        updated_device = make_device(user_id=user.id, is_trusted=True)
        updated_device.confirmed_at = datetime.now(UTC)

        with (
            patch("app.api.v1.endpoints.user_devices.crud_device.get_by_id", AsyncMock(return_value=device)),
            patch("app.api.v1.endpoints.user_devices.crud_device.update", AsyncMock(return_value=updated_device)) as mock_update,
        ):
            await CONFIRM_DEVICE(request=request, device_id=uuid4(), current_user=user, db=db)

        update_payload = mock_update.await_args.kwargs["device_in"]
        assert update_payload.is_trusted is True
        assert isinstance(update_payload.confirmed_at, datetime)
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_revoke_all_devices_commits_after_bulk_delete(self):
        db = AsyncMock()
        user = MagicMock(id=uuid4())
        request = Mock()
        request.state = Mock()

        with patch("app.api.v1.endpoints.user_devices.crud_device.bulk_delete_by_user", AsyncMock(return_value=3)):
            result = await REVOKE_ALL_DEVICES(request=request, current_user=user, db=db)

        assert result["revoked_count"] == 3
        db.commit.assert_awaited_once()
