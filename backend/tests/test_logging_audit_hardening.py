import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import HTTPException, Response
from starlette.requests import Request
from starlette.responses import Response as StarletteResponse

from app.api.v1.endpoints.auth import login_with_otp
from app.audit.constants import ActionType
from app.audit.middleware import AuditMiddleware
from app.audit.models import StudentAuditLog
from app.audit.utils import extract_query_params, should_audit

pytestmark = pytest.mark.smoke


def make_request(
    *,
    method: str = "POST",
    path: str = "/api/v1/auth/otp",
    body: dict | None = None,
    headers: dict[str, str] | None = None,
    query_string: str = "",
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
        "query_string": query_string.encode("utf-8"),
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


def test_should_not_audit_csrf_token():
    assert should_audit("/api/v1/auth/csrf-token") is False


def test_should_not_audit_fingerprint_mode():
    assert should_audit("/api/v1/auth/fingerprint-mode") is False


def test_should_audit_explicit_auth_paths():
    assert should_audit("/api/v1/auth/otp") is True
    assert should_audit("/api/v1/auth/dev-login") is True
    assert should_audit("/api/v1/auth/logout") is True


def test_extract_query_params_masks_sensitive_values_and_truncates() -> None:
    long_value = "x" * 300
    request = make_request(
        method="GET",
        path="/api/v1/student/profile",
        query_string=f"token=secret-token&search={long_value}",
    )

    result = extract_query_params(request)

    assert result == {
        "token": "[REDACTED]",
        "search": long_value[:160] + "...[TRUNCATED]",
    }


@pytest.mark.asyncio
async def test_audit_middleware_skips_excluded_path_without_writing() -> None:
    request = make_request(method="GET", path="/api/v1/auth/csrf-token")
    middleware = AuditMiddleware(app=MagicMock())

    mock_service = MagicMock()
    mock_service.write_log_sync = AsyncMock()
    mock_service.write_log = AsyncMock()

    async def call_next(_: Request):
        return StarletteResponse(status_code=200)

    with patch("app.audit.middleware.get_audit_service", return_value=mock_service):
        response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200
    mock_service.write_log_sync.assert_not_called()
    mock_service.write_log.assert_not_called()


def test_audit_jsonb_columns_store_none_as_sql_null():
    assert StudentAuditLog.__table__.c.query_params.type.none_as_null is True
    assert StudentAuditLog.__table__.c.request_body.type.none_as_null is True
    assert StudentAuditLog.__table__.c.fingerprint.type.none_as_null is True
    assert StudentAuditLog.__table__.c.extra_data.type.none_as_null is True


@pytest.mark.asyncio
async def test_login_with_otp_logs_only_masked_code():
    request = make_request(body={"otp": "489786"})

    csrf_protect = AsyncMock()
    redis = AsyncMock()
    redis.get.return_value = None

    with patch("app.api.v1.endpoints.auth.logger") as mock_logger, pytest.raises(HTTPException) as exc_info:
        await login_with_otp(
            request=request,
            response=Response(),
            otp="489786",
            remember_device=False,
            db=AsyncMock(),
            redis=redis,
            csrf_protect=csrf_protect,
        )

    assert exc_info.value.status_code == 400
    flattened_calls = "\n".join(str(call) for call in mock_logger.mock_calls)
    assert "489786" not in flattened_calls
    assert "48****" in flattened_calls


@pytest.mark.asyncio
@pytest.mark.smoke
async def test_audit_middleware_preserves_action_type_and_sanitizes_body():
    request = make_request(body={"otp": "489786", "remember_device": True})
    middleware = AuditMiddleware(app=MagicMock())

    mock_service = MagicMock()
    mock_service.is_security_critical.side_effect = lambda action: action == ActionType.AUTH_LOGIN.value
    mock_service.write_log_sync = AsyncMock()
    mock_service.write_log = AsyncMock()

    async def call_next(inner_request: Request):
        inner_request.state.audit_context.action_type = ActionType.AUTH_LOGIN.value
        return StarletteResponse(status_code=400)

    with patch("app.audit.middleware.get_audit_service", return_value=mock_service):
        response = await middleware.dispatch(request, call_next)

    assert response.status_code == 400
    mock_service.write_log_sync.assert_awaited_once()
    mock_service.write_log.assert_not_called()

    audit_context = mock_service.write_log_sync.await_args.args[0]
    assert audit_context.action_type == ActionType.AUTH_LOGIN.value
    assert audit_context.response_status == 400
    assert audit_context.request_body == {"otp": "[REDACTED]"}


@pytest.mark.asyncio
@pytest.mark.smoke
async def test_audit_middleware_tolerates_missing_fingerprint_header() -> None:
    request = make_request(body={"otp": "489786"})
    middleware = AuditMiddleware(app=MagicMock())

    mock_service = MagicMock()
    mock_service.is_security_critical.return_value = True
    mock_service.write_log_sync = AsyncMock()
    mock_service.write_log = AsyncMock()

    async def call_next(_: Request):
        return StarletteResponse(status_code=200)

    with patch("app.audit.middleware.get_audit_service", return_value=mock_service):
        response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200
    audit_context = mock_service.write_log_sync.await_args.args[0]
    assert audit_context.fingerprint is None


@pytest.mark.asyncio
async def test_audit_middleware_stores_compact_fingerprint() -> None:
    fingerprint_header = json.dumps(
        {
            "schema": "fingerprint-migration-v1",
            "kind": "normalized_replacement",
            "summary": {"platform": "Windows", "browser": "Chrome", "screen": {"width": 1920, "height": 1080}},
            "matching": {
                "platform": "Win32",
                "hardwareConcurrency": 8,
                "screen": {"width": 1920, "height": 1080, "colorDepth": 24},
                "webgl": {"vendor": "Google", "renderer": "ANGLE"},
                "canvas": "canvas-hash",
                "userAgent": "Chrome",
            },
            "raw": {"components": {"huge": True}},
        }
    )
    request = make_request(
        body={"otp": "489786"},
        headers={"X-Device-Fingerprint": fingerprint_header},
    )
    middleware = AuditMiddleware(app=MagicMock())

    mock_service = MagicMock()
    mock_service.is_security_critical.return_value = True
    mock_service.write_log_sync = AsyncMock()
    mock_service.write_log = AsyncMock()

    async def call_next(_: Request):
        return StarletteResponse(status_code=200)

    with patch("app.audit.middleware.get_audit_service", return_value=mock_service):
        response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200
    audit_context = mock_service.write_log_sync.await_args.args[0]
    assert audit_context.fingerprint is not None
    assert audit_context.fingerprint["kind"] == "normalized_replacement"
    assert "raw_payload" not in audit_context.fingerprint
    assert audit_context.fingerprint["normalized_summary"]["platform"] == "Windows"
    assert audit_context.fingerprint["normalized_matching"]["canvas"] == "canvas-hash"
