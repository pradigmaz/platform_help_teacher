from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import Response
from starlette.requests import Request

from app.api.v1.endpoints.admin_impersonate import (
    ADMIN_SESSION_COOKIE,
    ADMIN_TOKEN_COOKIE,
    IMPERSONATE_TOKEN_TTL_MINUTES,
    exit_impersonation,
    impersonate_user,
)
from app.audit.middleware import SESSION_COOKIE_NAME
from app.core import security
from app.models import User, UserRole


def make_request(
    *,
    path: str,
    cookies: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> Request:
    raw_headers = []
    if cookies:
        cookie_header = "; ".join(f"{key}={value}" for key, value in cookies.items())
        raw_headers.append((b"cookie", cookie_header.encode("latin-1")))
    for key, value in (headers or {}).items():
        raw_headers.append((key.lower().encode("latin-1"), value.encode("latin-1")))

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": b"",
        "headers": raw_headers,
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
        "state": {},
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    return Request(scope, receive)


def make_user(*, role: UserRole) -> User:
    return User(
        id=uuid4(),
        full_name=f"{role.value.title()} User",
        username=f"{role.value}_user",
        role=role,
        is_active=True,
    )


@pytest.mark.asyncio
async def test_exit_impersonation_restores_saved_admin_session_when_valid() -> None:
    admin_user = make_user(role=UserRole.ADMIN)
    original_token = security.create_access_token(admin_user.id, role=admin_user.role.value)
    request = make_request(
        path="/api/v1/admin/impersonate/exit",
        cookies={
            ADMIN_TOKEN_COOKIE: original_token,
            ADMIN_SESSION_COOKIE: "admin-session-id",
            SESSION_COOKIE_NAME: "imp-session-id",
        },
    )
    response = Response()
    db = AsyncMock()
    db.execute.return_value = Mock(scalar_one_or_none=Mock(return_value=admin_user))

    with (
        patch(
            "app.api.v1.endpoints.admin_impersonate.session_service.validate_session",
            new=AsyncMock(return_value={"user_id": str(admin_user.id)}),
        ) as mock_validate,
        patch(
            "app.api.v1.endpoints.admin_impersonate.session_service.revoke_session",
            new=AsyncMock(),
        ) as mock_revoke,
        patch(
            "app.api.v1.endpoints.admin_impersonate.session_service.create_session",
            new=AsyncMock(),
        ) as mock_create,
    ):
        result = await exit_impersonation(request=request, response=response, db=db)

    assert result == {"message": "Returned to admin session"}
    mock_validate.assert_awaited_once_with("admin-session-id", expected_user_id=str(admin_user.id))
    mock_revoke.assert_awaited_once_with("imp-session-id")
    mock_create.assert_not_awaited()
    set_cookies = response.headers.getlist("set-cookie")
    assert any(f"access_token={original_token}" in header for header in set_cookies)
    assert any(f"{SESSION_COOKIE_NAME}=admin-session-id" in header for header in set_cookies)


@pytest.mark.asyncio
async def test_exit_impersonation_creates_fresh_admin_session_when_original_missing() -> None:
    admin_user = make_user(role=UserRole.ADMIN)
    original_token = security.create_access_token(admin_user.id, role=admin_user.role.value)
    request = make_request(
        path="/api/v1/admin/impersonate/exit",
        cookies={
            ADMIN_TOKEN_COOKIE: original_token,
            ADMIN_SESSION_COOKIE: "stale-admin-session",
            SESSION_COOKIE_NAME: "imp-session-id",
        },
        headers={"X-Device-Fingerprint": '{"platform":"Win32"}'},
    )
    response = Response()
    db = AsyncMock()
    db.execute.return_value = Mock(scalar_one_or_none=Mock(return_value=admin_user))

    with (
        patch(
            "app.api.v1.endpoints.admin_impersonate.session_service.validate_session",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "app.api.v1.endpoints.admin_impersonate.session_service.revoke_session",
            new=AsyncMock(),
        ) as mock_revoke,
        patch(
            "app.api.v1.endpoints.admin_impersonate.session_service.create_session",
            new=AsyncMock(),
        ) as mock_create,
    ):
        result = await exit_impersonation(request=request, response=response, db=db)

    assert result == {"message": "Returned to admin session"}
    mock_revoke.assert_awaited_once_with("imp-session-id")
    mock_create.assert_awaited_once()
    created_session_id = mock_create.await_args.kwargs["session_id"]
    assert mock_create.await_args.kwargs["user_id"] == admin_user.id
    assert mock_create.await_args.kwargs["device_fingerprint"] == '{"platform":"Win32"}'
    assert mock_create.await_args.kwargs["ip_address"] == "127.0.0.1"
    assert any(
        f"{SESSION_COOKIE_NAME}={created_session_id}" in header for header in response.headers.getlist("set-cookie")
    )


@pytest.mark.asyncio
async def test_impersonate_user_stashes_original_session_cookie() -> None:
    admin_user = make_user(role=UserRole.ADMIN)
    target_user = make_user(role=UserRole.STUDENT)
    original_token = security.create_access_token(admin_user.id, role=admin_user.role.value)
    request = make_request(
        path=f"/api/v1/admin/impersonate/{target_user.id}",
        cookies={
            "access_token": original_token,
            SESSION_COOKIE_NAME: "admin-session-id",
        },
    )
    response = Response()
    db = AsyncMock()
    db.execute.return_value = Mock(scalar_one_or_none=Mock(return_value=target_user))

    with patch(
        "app.api.v1.endpoints.admin_impersonate.session_service.create_session",
        new=AsyncMock(),
    ) as mock_create:
        result = await impersonate_user(
            user_id=target_user.id,
            request=request,
            response=response,
            db=db,
            admin=admin_user,
        )

    assert result["user"]["id"] == str(target_user.id)
    assert mock_create.await_args.kwargs["user_id"] == target_user.id
    assert mock_create.await_args.kwargs["is_impersonation"] is True
    set_cookies = response.headers.getlist("set-cookie")
    assert any(f"{ADMIN_TOKEN_COOKIE}={original_token}" in header for header in set_cookies)
    assert any(f"{ADMIN_SESSION_COOKIE}=admin-session-id" in header for header in set_cookies)
    assert any(SESSION_COOKIE_NAME in header for header in set_cookies)
    assert any(
        f"{ADMIN_SESSION_COOKIE}=admin-session-id" in header
        and f"Max-Age={IMPERSONATE_TOKEN_TTL_MINUTES * 60}" in header
        for header in set_cookies
    )
