from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.api.v1.endpoints.admin_impersonate import (
    ADMIN_SESSION_COOKIE,
    ADMIN_TOKEN_COOKIE,
    exit_impersonation,
    impersonate_user,
)
from app.audit.middleware import SESSION_COOKIE_NAME
from app.core import security
from app.models import User, UserRole

pytestmark = pytest.mark.smoke


def create_mock_user(*, user_id: UUID | None = None, role: UserRole, is_active: bool = True) -> User:
    if user_id is None:
        user_id = uuid4()

    return User(
        id=user_id,
        full_name=f"{role.value.title()} User",
        username=f"{role.value}_user",
        role=role,
        is_active=is_active,
    )


def create_mock_request(
    *,
    cookies: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    client_host: str = "127.0.0.1",
) -> Mock:
    request = Mock(spec=Request)
    request.cookies = cookies or {}
    request.headers = headers or {}
    request.client = Mock(host=client_host)
    return request


def get_set_cookie_header(response: Response, cookie_name: str) -> str | None:
    prefix = f"{cookie_name}="
    for header_name, header_value in response.raw_headers:
        if header_name == b"set-cookie":
            decoded = header_value.decode("latin-1")
            if decoded.startswith(prefix):
                return decoded
    return None


@pytest.mark.asyncio
async def test_impersonate_user_preserves_original_admin_session_cookie() -> None:
    admin = create_mock_user(role=UserRole.ADMIN)
    target_user = create_mock_user(role=UserRole.STUDENT)
    request = create_mock_request(
        cookies={
            "access_token": "admin-token",
            SESSION_COOKIE_NAME: "admin-session-id",
        },
        headers={"X-Device-Fingerprint": "device-fp"},
    )
    response = Response()
    db = AsyncMock(spec=AsyncSession)
    db.execute.return_value = Mock(scalar_one_or_none=Mock(return_value=target_user))
    impersonation_session_uuid = UUID("00000000-0000-0000-0000-000000000111")

    with (
        patch("app.api.v1.endpoints.admin_impersonate.settings.ENVIRONMENT", "development"),
        patch("app.api.v1.endpoints.admin_impersonate.uuid4", return_value=impersonation_session_uuid),
        patch(
            "app.api.v1.endpoints.admin_impersonate.session_service.create_session",
            new=AsyncMock(return_value=True),
        ) as mock_create_session,
    ):
        result = await impersonate_user(
            user_id=target_user.id,
            request=request,
            response=response,
            db=db,
            admin=admin,
        )

    assert result["message"] == "Impersonation successful"
    admin_token_cookie = get_set_cookie_header(response, ADMIN_TOKEN_COOKIE)
    admin_session_cookie = get_set_cookie_header(response, ADMIN_SESSION_COOKIE)
    impersonation_session_cookie = get_set_cookie_header(response, SESSION_COOKIE_NAME)

    assert admin_token_cookie is not None
    assert admin_token_cookie.startswith(f"{ADMIN_TOKEN_COOKIE}=admin-token;")
    assert "HttpOnly" in admin_token_cookie
    assert "Path=/" in admin_token_cookie

    assert admin_session_cookie is not None
    assert admin_session_cookie.startswith(f"{ADMIN_SESSION_COOKIE}=admin-session-id;")
    assert "HttpOnly" in admin_session_cookie
    assert "Path=/" in admin_session_cookie

    assert impersonation_session_cookie is not None
    assert impersonation_session_cookie.startswith(f"{SESSION_COOKIE_NAME}={impersonation_session_uuid};")
    assert "HttpOnly" in impersonation_session_cookie
    mock_create_session.assert_awaited_once_with(
        user_id=target_user.id,
        session_id=str(impersonation_session_uuid),
        device_fingerprint="device-fp",
        ip_address="127.0.0.1",
        is_impersonation=True,
    )


@pytest.mark.asyncio
async def test_exit_impersonation_restores_original_admin_session_cookie() -> None:
    admin = create_mock_user(role=UserRole.ADMIN)
    original_token = security.create_access_token(admin.id, role=admin.role.value)
    request = create_mock_request(
        cookies={
            ADMIN_TOKEN_COOKIE: original_token,
            ADMIN_SESSION_COOKIE: "admin-session-id",
            SESSION_COOKIE_NAME: "impersonation-session-id",
        }
    )
    response = Response()
    db = AsyncMock(spec=AsyncSession)
    db.execute.return_value = Mock(scalar_one_or_none=Mock(return_value=admin))

    with (
        patch("app.api.v1.endpoints.admin_impersonate.settings.ENVIRONMENT", "development"),
        patch(
            "app.api.v1.endpoints.admin_impersonate.session_service.validate_session",
            new=AsyncMock(return_value={"user_id": str(admin.id), "is_impersonation": False}),
        ) as mock_validate_session,
        patch(
            "app.api.v1.endpoints.admin_impersonate.session_service.revoke_session",
            new=AsyncMock(return_value=True),
        ) as mock_revoke_session,
        patch(
            "app.api.v1.endpoints.admin_impersonate.session_service.create_session",
            new=AsyncMock(return_value=True),
        ) as mock_create_session,
    ):
        result = await exit_impersonation(
            request=request,
            response=response,
            db=db,
        )

    assert result == {"message": "Returned to admin session"}
    restored_token_cookie = get_set_cookie_header(response, "access_token")
    restored_session_cookie = get_set_cookie_header(response, SESSION_COOKIE_NAME)
    deleted_admin_token_cookie = get_set_cookie_header(response, ADMIN_TOKEN_COOKIE)
    deleted_admin_session_cookie = get_set_cookie_header(response, ADMIN_SESSION_COOKIE)

    assert restored_token_cookie is not None
    assert restored_token_cookie.startswith(f"access_token={original_token};")
    assert "HttpOnly" in restored_token_cookie
    assert "Path=/" in restored_token_cookie

    assert restored_session_cookie is not None
    assert restored_session_cookie.startswith(f"{SESSION_COOKIE_NAME}=admin-session-id;")
    assert "HttpOnly" in restored_session_cookie
    assert "Path=/" in restored_session_cookie

    assert deleted_admin_token_cookie is not None
    assert deleted_admin_token_cookie.startswith(f'{ADMIN_TOKEN_COOKIE}="";')
    assert "Max-Age=0" in deleted_admin_token_cookie
    assert "Path=/" in deleted_admin_token_cookie

    assert deleted_admin_session_cookie is not None
    assert deleted_admin_session_cookie.startswith(f'{ADMIN_SESSION_COOKIE}="";')
    assert "Max-Age=0" in deleted_admin_session_cookie
    assert "Path=/" in deleted_admin_session_cookie
    mock_validate_session.assert_awaited_once_with("admin-session-id", expected_user_id=str(admin.id))
    mock_revoke_session.assert_awaited_once_with("impersonation-session-id")
    mock_create_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_exit_impersonation_creates_new_admin_session_when_original_is_missing() -> None:
    admin = create_mock_user(role=UserRole.ADMIN)
    original_token = security.create_access_token(admin.id, role=admin.role.value)
    request = create_mock_request(
        cookies={
            ADMIN_TOKEN_COOKIE: original_token,
            ADMIN_SESSION_COOKIE: "stale-admin-session",
            SESSION_COOKIE_NAME: "impersonation-session-id",
        },
        headers={"X-Device-Fingerprint": "restored-device-fp"},
        client_host="10.10.10.10",
    )
    response = Response()
    db = AsyncMock(spec=AsyncSession)
    db.execute.return_value = Mock(scalar_one_or_none=Mock(return_value=admin))
    restored_session_uuid = UUID("00000000-0000-0000-0000-000000000222")

    with (
        patch("app.api.v1.endpoints.admin_impersonate.settings.ENVIRONMENT", "development"),
        patch("app.api.v1.endpoints.admin_impersonate.uuid4", return_value=restored_session_uuid),
        patch(
            "app.api.v1.endpoints.admin_impersonate.session_service.validate_session",
            new=AsyncMock(return_value=None),
        ) as mock_validate_session,
        patch(
            "app.api.v1.endpoints.admin_impersonate.session_service.revoke_session",
            new=AsyncMock(return_value=True),
        ) as mock_revoke_session,
        patch(
            "app.api.v1.endpoints.admin_impersonate.session_service.create_session",
            new=AsyncMock(return_value=True),
        ) as mock_create_session,
    ):
        result = await exit_impersonation(
            request=request,
            response=response,
            db=db,
        )

    assert result == {"message": "Returned to admin session"}
    restored_session_cookie = get_set_cookie_header(response, SESSION_COOKIE_NAME)

    assert restored_session_cookie is not None
    assert restored_session_cookie.startswith(f"{SESSION_COOKIE_NAME}={restored_session_uuid};")
    assert "HttpOnly" in restored_session_cookie
    assert "Path=/" in restored_session_cookie
    mock_validate_session.assert_awaited_once_with("stale-admin-session", expected_user_id=str(admin.id))
    mock_revoke_session.assert_awaited_once_with("impersonation-session-id")
    mock_create_session.assert_awaited_once_with(
        user_id=admin.id,
        session_id=str(restored_session_uuid),
        device_fingerprint="restored-device-fp",
        ip_address="10.10.10.10",
    )
