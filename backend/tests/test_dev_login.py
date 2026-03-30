import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, Response
from starlette.requests import Request

from app.api.v1.endpoints.auth import (
    DEV_LOGIN_FULL_NAME,
    DEV_LOGIN_USERNAME,
    login_with_dev_account,
)
from app.models.user import UserRole

pytestmark = pytest.mark.smoke


def make_request(
    *,
    method: str = "POST",
    path: str = "/api/v1/auth/dev-login",
    body: dict | None = None,
    headers: dict[str, str] | None = None,
) -> Request:
    payload = json.dumps(body or {}).encode("utf-8")
    raw_headers = []
    for key, value in (headers or {}).items():
        raw_headers.append((key.lower().encode("latin-1"), value.encode("latin-1")))

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": b"",
        "headers": raw_headers,
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
        "state": {},
    }

    sent = False

    async def receive():
        nonlocal sent
        if sent:
            return {"type": "http.request", "body": b"", "more_body": False}
        sent = True
        return {"type": "http.request", "body": payload, "more_body": False}

    return Request(scope, receive)


@pytest.mark.asyncio
async def test_dev_login_returns_404_outside_development():
    request = make_request(body={"remember_device": True})
    csrf_protect = AsyncMock()
    db = AsyncMock()

    with patch("app.api.v1.endpoints.auth.settings.ENVIRONMENT", "production"):
        with pytest.raises(HTTPException) as exc_info:
            await login_with_dev_account(
                request=request,
                response=Response(),
                remember_device=True,
                db=db,
                csrf_protect=csrf_protect,
            )

    assert exc_info.value.status_code == 404
    csrf_protect.validate_csrf.assert_not_awaited()
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_dev_login_creates_admin_user_if_missing():
    request = make_request(body={"remember_device": True})
    csrf_protect = AsyncMock()
    db = AsyncMock()
    db.add = Mock()
    db.execute.return_value = Mock(scalar_one_or_none=Mock(return_value=None))
    response = Response()

    with patch("app.api.v1.endpoints.auth.settings.ENVIRONMENT", "development"):
        with patch("app.api.v1.endpoints.auth._complete_login", new=AsyncMock(return_value={"ok": True})) as mock_complete:
            result = await login_with_dev_account(
                request=request,
                response=response,
                remember_device=True,
                db=db,
                csrf_protect=csrf_protect,
            )

    assert result == {"ok": True}
    csrf_protect.validate_csrf.assert_awaited_once_with(request)
    db.add.assert_called_once()
    created_user = db.add.call_args.args[0]
    assert created_user.username == DEV_LOGIN_USERNAME
    assert created_user.full_name == DEV_LOGIN_FULL_NAME
    assert created_user.role == UserRole.ADMIN
    assert created_user.is_active is True
    assert created_user.onboarding_completed is True
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(created_user)
    mock_complete.assert_awaited_once_with(
        request=request,
        response=response,
        user=created_user,
        remember_device=True,
        db=db,
    )


@pytest.mark.asyncio
async def test_dev_login_upgrades_existing_user_before_login():
    request = make_request(body={"remember_device": False})
    csrf_protect = AsyncMock()
    db = AsyncMock()
    db.add = Mock()
    response = Response()
    existing_user = Mock(
        username=DEV_LOGIN_USERNAME,
        full_name="Old User",
        role=UserRole.STUDENT,
        is_active=False,
        onboarding_completed=False,
    )
    db.execute.return_value = Mock(scalar_one_or_none=Mock(return_value=existing_user))

    with patch("app.api.v1.endpoints.auth.settings.ENVIRONMENT", "development"):
        with patch("app.api.v1.endpoints.auth._complete_login", new=AsyncMock(return_value={"ok": True})) as mock_complete:
            result = await login_with_dev_account(
                request=request,
                response=response,
                remember_device=False,
                db=db,
                csrf_protect=csrf_protect,
            )

    assert result == {"ok": True}
    assert existing_user.role == UserRole.ADMIN
    assert existing_user.is_active is True
    assert existing_user.onboarding_completed is True
    db.add.assert_called_once_with(existing_user)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(existing_user)
    mock_complete.assert_awaited_once_with(
        request=request,
        response=response,
        user=existing_user,
        remember_device=False,
        db=db,
    )
