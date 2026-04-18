from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.api.v1.endpoints.auth import get_auth_status


def make_request(*, cookies: dict[str, str] | None = None, path: str = "/api/v1/auth/status") -> Request:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
        "state": {},
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    request = Request(scope, receive)
    request._cookies = cookies or {}
    return request


@pytest.mark.asyncio
async def test_auth_status_returns_anonymous_without_auth_cookies():
    request = make_request()
    db = AsyncMock()

    with patch("app.api.v1.endpoints.auth.get_current_user", new=AsyncMock()) as mock_get_current_user:
        payload = await get_auth_status(request=request, db=db)

    assert payload == {"authenticated": False, "user": None}
    mock_get_current_user.assert_not_awaited()


@pytest.mark.asyncio
async def test_auth_status_returns_anonymous_when_session_is_invalid():
    request = make_request(cookies={"access_token": "token", "audit_session_id": "session"})
    db = AsyncMock()

    with patch(
        "app.api.v1.endpoints.auth.get_current_user",
        new=AsyncMock(side_effect=HTTPException(status_code=401, detail="Session revoked")),
    ):
        payload = await get_auth_status(request=request, db=db)

    assert payload == {"authenticated": False, "user": None}


@pytest.mark.asyncio
async def test_auth_status_returns_user_for_valid_session():
    request = make_request(cookies={"access_token": "token", "audit_session_id": "session"})
    db = AsyncMock()
    user = Mock(id="user-1", full_name="Admin User", username="admin", role="admin")

    with patch("app.api.v1.endpoints.auth.get_current_user", new=AsyncMock(return_value=user)):
        payload = await get_auth_status(request=request, db=db)

    assert payload == {
        "authenticated": True,
        "user": {
            "id": "user-1",
            "full_name": "Admin User",
            "username": "admin",
            "role": "admin",
        },
    }
