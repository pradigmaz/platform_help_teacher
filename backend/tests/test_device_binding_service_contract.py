"""Service-level contracts for device registration/update persistence."""

import logging
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.services.device_service import parse_device_info, register_or_update_device
from tests.support.device_binding import make_fp_json, make_mock_device


class TestDeviceRegistrationServiceContract:
    @pytest.mark.asyncio
    async def test_register_calls_commit_after_create(self):
        db = AsyncMock()
        user_id = uuid4()

        with patch("app.services.device_service.crud_device") as mock_crud:
            mock_crud.get_by_fingerprint = AsyncMock(return_value=None)
            mock_crud.create = AsyncMock(return_value=make_mock_device(user_id=user_id))

            result = await register_or_update_device(db=db, user_id=user_id, device_fingerprint=make_fp_json())

        assert result is True
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_register_calls_commit_after_update(self):
        db = AsyncMock()
        user_id = uuid4()
        existing = make_mock_device(user_id=user_id)

        with patch("app.services.device_service.crud_device") as mock_crud:
            mock_crud.get_by_fingerprint = AsyncMock(return_value=existing)
            mock_crud.update = AsyncMock(return_value=existing)

            result = await register_or_update_device(db=db, user_id=user_id, device_fingerprint=make_fp_json())

        assert result is True
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_register_returns_false_on_error_and_rolls_back(self):
        db = AsyncMock()
        user_id = uuid4()

        with patch("app.services.device_service.crud_device") as mock_crud:
            mock_crud.get_by_fingerprint = AsyncMock(side_effect=Exception("DB constraint violation"))

            result = await register_or_update_device(db=db, user_id=user_id, device_fingerprint=make_fp_json())

        assert result is False
        db.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_empty_fingerprint_early_return(self):
        db = AsyncMock()

        result = await register_or_update_device(db=db, user_id=uuid4(), device_fingerprint=None)

        assert result is None
        db.commit.assert_not_called()
        db.flush.assert_not_called()
        db.rollback.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_json_fingerprint_early_return_without_warning(self, caplog):
        db = AsyncMock()
        caplog.set_level(logging.WARNING)

        result = await register_or_update_device(db=db, user_id=uuid4(), device_fingerprint="{}")

        assert result is None
        assert "Empty fingerprint" not in caplog.text

    def test_parse_device_info_empty_fingerprint_does_not_log_warning(self, caplog):
        caplog.set_level(logging.WARNING)

        result = parse_device_info(None)

        assert result["platform"] == "Unknown"
        assert "Empty fingerprint" not in caplog.text
