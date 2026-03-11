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
from app.audit.utils import should_audit


def make_request(
    *,
    method: str = "POST",
    path: str = "/api/v1/auth/otp",
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


def test_should_not_audit_csrf_token():
    assert should_audit("/api/v1/auth/csrf-token") is False


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

    with patch("app.api.v1.endpoints.auth.logger") as mock_logger:
        with pytest.raises(HTTPException) as exc_info:
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
