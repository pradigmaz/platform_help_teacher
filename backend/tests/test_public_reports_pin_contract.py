"""HTTP-level contract checks for public report PIN verification responses."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.api.deps import get_db
from app.api.v1.endpoints.public_reports import router
from app.services.pin_service import report_pin_service
from tests.support.http import router_client


@pytest.mark.asyncio
async def test_verify_pin_without_pin_returns_explicit_retry_after():
    mock_db = AsyncMock()
    report = SimpleNamespace(pin_hash=None)

    async def override_db():
        yield mock_db

    with (
        patch("app.api.v1.endpoints.public_reports.get_valid_report", AsyncMock(return_value=report)),
        patch.object(report_pin_service, "check_lockout", AsyncMock(return_value=None)),
    ):
        async with router_client(router, dependency_overrides={get_db: override_db}) as client:
            response = await client.post("/report/ABCDEFGH/verify-pin", json={"pin": "1234"})

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "No PIN required",
        "attempts_left": None,
        "retry_after": None,
    }


@pytest.mark.asyncio
async def test_verify_pin_success_returns_explicit_retry_after():
    mock_db = AsyncMock()
    report = SimpleNamespace(pin_hash="hashed-pin")

    async def override_db():
        yield mock_db

    with (
        patch("app.api.v1.endpoints.public_reports.get_valid_report", AsyncMock(return_value=report)),
        patch.object(report_pin_service, "check_lockout", AsyncMock(return_value=None)),
        patch.object(report_pin_service, "reset_attempts", AsyncMock(return_value=None)),
        patch("app.api.v1.endpoints.public_reports.get_redis", AsyncMock(return_value=None)),
        patch("app.api.v1.endpoints.public_reports.ReportService.verify_pin", return_value=True),
    ):
        async with router_client(router, dependency_overrides={get_db: override_db}) as client:
            response = await client.post("/report/ABCDEFGH/verify-pin", json={"pin": "1234"})

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "PIN verified",
        "attempts_left": None,
        "retry_after": None,
    }


@pytest.mark.asyncio
async def test_verify_pin_invalid_returns_explicit_retry_after():
    mock_db = AsyncMock()
    report = SimpleNamespace(pin_hash="hashed-pin")

    async def override_db():
        yield mock_db

    with (
        patch("app.api.v1.endpoints.public_reports.get_valid_report", AsyncMock(return_value=report)),
        patch.object(report_pin_service, "check_lockout", AsyncMock(return_value=None)),
        patch.object(report_pin_service, "increment_attempts", AsyncMock(return_value=3)),
        patch("app.api.v1.endpoints.public_reports.ReportService.verify_pin", return_value=False),
    ):
        async with router_client(router, dependency_overrides={get_db: override_db}) as client:
            response = await client.post("/report/ABCDEFGH/verify-pin", json={"pin": "9999"})

    assert response.status_code == 200
    assert response.json() == {
        "success": False,
        "message": "Invalid PIN",
        "attempts_left": 3,
        "retry_after": None,
    }
