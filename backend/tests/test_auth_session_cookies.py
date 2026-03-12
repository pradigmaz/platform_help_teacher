from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import Response
from starlette.requests import Request

from app.api.v1.endpoints.auth import _complete_login
from app.audit.middleware import SESSION_COOKIE_NAME
from app.core.config import settings
from app.models import User
from app.models.user import UserRole


def make_request() -> Request:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "path": "/api/v1/auth/otp",
        "raw_path": b"/api/v1/auth/otp",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
        "state": {},
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    return Request(scope, receive)


def make_user(role: UserRole) -> User:
    return User(
        id=uuid4(),
        full_name=f"{role.value.title()} User",
        username=f"{role.value}_user",
        role=role,
        is_active=True,
    )


@pytest.mark.asyncio
async def test_complete_login_force_session_cookie_disables_admin_persistence() -> None:
    request = make_request()
    response = Response()
    user = make_user(UserRole.ADMIN)

    with (
        patch(
            "app.api.v1.endpoints.auth.session_service.create_session",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "app.api.v1.endpoints.auth.device_service.register_or_update_device",
            new=AsyncMock(return_value=True),
        ),
    ):
        await _complete_login(
            request=request,
            response=response,
            user=user,
            remember_device=False,
            force_session_cookie=True,
            db=AsyncMock(),
        )

    set_cookies = response.headers.getlist("set-cookie")
    assert any(header.startswith("access_token=") and "Max-Age" not in header for header in set_cookies)
    assert any(header.startswith(f"{SESSION_COOKIE_NAME}=") and "Max-Age" not in header for header in set_cookies)


@pytest.mark.asyncio
async def test_complete_login_keeps_admin_persistent_without_force_session_cookie() -> None:
    request = make_request()
    response = Response()
    user = make_user(UserRole.ADMIN)

    with (
        patch(
            "app.api.v1.endpoints.auth.session_service.create_session",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "app.api.v1.endpoints.auth.device_service.register_or_update_device",
            new=AsyncMock(return_value=True),
        ),
    ):
        await _complete_login(
            request=request,
            response=response,
            user=user,
            remember_device=False,
            db=AsyncMock(),
        )

    expected_max_age = f"Max-Age={settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60}"
    set_cookies = response.headers.getlist("set-cookie")
    assert any(header.startswith("access_token=") and expected_max_age in header for header in set_cookies)
    assert any(header.startswith(f"{SESSION_COOKIE_NAME}=") and expected_max_age in header for header in set_cookies)
