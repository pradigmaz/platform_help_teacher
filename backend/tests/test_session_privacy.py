import json
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from app.api.v1.endpoints.user_sessions import get_my_sessions
from app.audit.middleware import SESSION_COOKIE_NAME
from app.services import session_service

GET_MY_SESSIONS = get_my_sessions.__wrapped__


def _make_fingerprint(user_agent: str = "Mozilla/5.0 Chrome/122.0.0.0 Safari/537.36") -> str:
    return json.dumps(
        {
            "platform": "Win32",
            "userAgent": user_agent,
            "screen": {"width": 1920, "height": 1080},
        }
    )


@pytest.mark.asyncio
async def test_create_session_stores_device_summary_without_raw_fingerprint() -> None:
    user_id = uuid4()
    session_id = "privacy-safe-session"
    raw_fingerprint = _make_fingerprint()
    redis = AsyncMock()
    redis.eval.return_value = 0

    with patch("app.services.session_service.get_redis", new=AsyncMock(return_value=redis)):
        created = await session_service.create_session(
            user_id=user_id,
            session_id=session_id,
            device_fingerprint=raw_fingerprint,
            ip_address="192.168.1.25",
        )

    assert created is True
    stored_key, stored_ttl, stored_payload = redis.setex.await_args.args
    stored_session = json.loads(stored_payload)
    assert stored_key == f"{session_service.SESSION_PREFIX}{session_id}"
    assert stored_ttl == session_service.SESSION_TTL
    assert stored_session["user_id"] == str(user_id)
    assert stored_session["device_summary"] == {
        "platform": "Windows",
        "browser": "Chrome",
        "userAgent": "Chrome",
        "screen": {"width": 1920, "height": 1080},
    }
    assert stored_session["ip_address"] == "192.168.x.x"
    assert "device_fingerprint" not in stored_session
    assert raw_fingerprint not in stored_payload


@pytest.mark.asyncio
async def test_get_my_sessions_reads_new_device_summary() -> None:
    request = Mock()
    request.cookies = {SESSION_COOKIE_NAME: "current-session"}
    current_user = Mock(id=uuid4())

    with patch(
        "app.api.v1.endpoints.user_sessions.session_service.get_user_sessions",
        new=AsyncMock(
            return_value=[
                {
                    "session_id": "current-session",
                    "created_at": "2026-03-12T12:00:00+00:00",
                    "device_summary": {
                        "platform": "Win32",
                        "userAgent": "Chrome",
                        "screen": {"width": 1920, "height": 1080},
                    },
                    "ip_address": "192.168.1.25",
                    "is_impersonation": False,
                }
            ]
        ),
    ):
        response = await GET_MY_SESSIONS(request=request, current_user=current_user)

    session = response.sessions[0]
    assert session.device.platform == "Windows"
    assert session.device.browser == "Chrome"
    assert session.device.screen == "1920×1080"
    assert session.ip_address == "192.168.x.x"
    assert session.is_current is True


@pytest.mark.asyncio
async def test_get_my_sessions_reads_canonical_device_summary() -> None:
    request = Mock()
    request.cookies = {}
    current_user = Mock(id=uuid4())

    with patch(
        "app.api.v1.endpoints.user_sessions.session_service.get_user_sessions",
        new=AsyncMock(
            return_value=[
                {
                    "session_id": "canonical-session",
                    "created_at": "2026-03-12T12:30:00+00:00",
                    "device_summary": {
                        "platform": "Windows",
                        "browser": "Chrome",
                        "screen": {"width": 1920, "height": 1080},
                    },
                    "ip_address": "192.168.1.30",
                    "is_impersonation": False,
                }
            ]
        ),
    ):
        response = await GET_MY_SESSIONS(request=request, current_user=current_user)

    session = response.sessions[0]
    assert session.device.platform == "Windows"
    assert session.device.browser == "Chrome"
    assert session.device.screen == "1920×1080"


@pytest.mark.asyncio
async def test_get_my_sessions_reads_edge_device_summary() -> None:
    request = Mock()
    request.cookies = {}
    current_user = Mock(id=uuid4())

    with patch(
        "app.api.v1.endpoints.user_sessions.session_service.get_user_sessions",
        new=AsyncMock(
            return_value=[
                {
                    "session_id": "edge-session",
                    "created_at": "2026-03-12T13:00:00+00:00",
                    "device_summary": {
                        "platform": "Win32",
                        "userAgent": "Edge",
                        "screen": {"width": 1920, "height": 1080},
                    },
                    "ip_address": "172.16.0.12",
                    "is_impersonation": False,
                }
            ]
        ),
    ):
        response = await GET_MY_SESSIONS(request=request, current_user=current_user)

    session = response.sessions[0]
    assert session.device.platform == "Windows"
    assert session.device.browser == "Edge"
    assert session.device.screen == "1920×1080"
    assert session.ip_address == "172.16.x.x"
    assert session.is_current is False


@pytest.mark.asyncio
async def test_get_my_sessions_reads_legacy_device_fingerprint() -> None:
    request = Mock()
    request.cookies = {}
    current_user = Mock(id=uuid4())

    with patch(
        "app.api.v1.endpoints.user_sessions.session_service.get_user_sessions",
        new=AsyncMock(
            return_value=[
                {
                    "session_id": "legacy-session",
                    "created_at": "2026-03-11T12:00:00+00:00",
                    "device_fingerprint": _make_fingerprint(user_agent="Mozilla/5.0 Firefox/123.0"),
                    "ip_address": "10.0.0.7",
                    "is_impersonation": False,
                }
            ]
        ),
    ):
        response = await GET_MY_SESSIONS(request=request, current_user=current_user)

    session = response.sessions[0]
    assert session.device.platform == "Windows"
    assert session.device.browser == "Firefox"
    assert session.device.screen == "1920×1080"
    assert session.ip_address == "10.0.x.x"
    assert session.is_current is False


@pytest.mark.asyncio
async def test_create_impersonation_session_is_tracked_for_user_revocation() -> None:
    user_id = uuid4()
    redis = AsyncMock()

    with patch("app.services.session_service.get_redis", new=AsyncMock(return_value=redis)):
        created = await session_service.create_session(
            user_id=user_id,
            session_id="impersonation-session",
            is_impersonation=True,
        )

    assert created is True
    redis.sadd.assert_awaited_once_with(
        f"{session_service.USER_SESSIONS_PREFIX}{user_id}",
        "impersonation-session",
    )
    redis.expire.assert_awaited_once_with(
        f"{session_service.USER_SESSIONS_PREFIX}{user_id}",
        session_service.SESSION_TTL,
    )
    redis.eval.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_my_sessions_sorts_current_session_first() -> None:
    request = Mock()
    request.cookies = {SESSION_COOKIE_NAME: "current-session"}
    current_user = Mock(id=uuid4())

    with patch(
        "app.api.v1.endpoints.user_sessions.session_service.get_user_sessions",
        new=AsyncMock(
            return_value=[
                {
                    "session_id": "older-session",
                    "created_at": "2026-03-12T12:00:00+00:00",
                    "device_summary": {"platform": "Win32", "userAgent": "Chrome", "screen": {}},
                    "ip_address": "192.168.1.10",
                    "is_impersonation": False,
                },
                {
                    "session_id": "current-session",
                    "created_at": "2026-03-12T11:00:00+00:00",
                    "device_summary": {"platform": "Win32", "userAgent": "Chrome", "screen": {}},
                    "ip_address": "192.168.1.11",
                    "is_impersonation": False,
                },
            ]
        ),
    ):
        response = await GET_MY_SESSIONS(request=request, current_user=current_user)

    assert [session.session_id for session in response.sessions] == ["current-session", "older-session"]
