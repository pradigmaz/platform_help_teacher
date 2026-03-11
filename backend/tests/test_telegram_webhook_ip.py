from unittest.mock import MagicMock, Mock

import pytest
from fastapi import HTTPException, Request

from app.api.deps import verify_telegram_ip
from app.core.client_ip import extract_client_ip
from app.core.limiter import get_rate_limit_ip
from app.middleware.ip_ban import IPBanMiddleware
from app.middleware.security_monitor import SecurityMonitorMiddleware


def create_mock_webhook_request(
    client_ip: str,
    headers: dict[str, str] | None = None,
    path: str = "/api/v1/webhooks/telegram",
) -> Mock:
    request = Mock(spec=Request)
    request.client = Mock(host=client_ip)
    request.url = Mock(path=path)
    request.headers = headers or {}
    return request


@pytest.mark.asyncio
async def test_verify_telegram_ip_allows_direct_telegram_source():
    request = create_mock_webhook_request(client_ip="91.108.5.53")

    await verify_telegram_ip(request)


@pytest.mark.asyncio
async def test_verify_telegram_ip_allows_cloudflare_proxied_telegram_source():
    request = create_mock_webhook_request(
        client_ip="104.21.87.138",
        headers={
            "CF-Connecting-IP": "91.108.5.53",
            "X-Forwarded-For": "104.21.87.138",
        },
    )

    await verify_telegram_ip(request)


@pytest.mark.asyncio
async def test_verify_telegram_ip_rejects_non_telegram_source():
    request = create_mock_webhook_request(
        client_ip="104.21.87.138",
        headers={
            "CF-Connecting-IP": "203.0.113.10",
            "X-Forwarded-For": "104.21.87.138",
        },
    )

    with pytest.raises(HTTPException) as exc:
        await verify_telegram_ip(request)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_verify_telegram_ip_ignores_spoofed_cf_header_on_dns_only_webhook():
    request = create_mock_webhook_request(
        client_ip="172.19.0.3",
        headers={
            "X-Real-IP": "203.0.113.10",
            "X-Forwarded-For": "203.0.113.10",
            "CF-Connecting-IP": "91.108.5.53",
        },
    )

    with pytest.raises(HTTPException) as exc:
        await verify_telegram_ip(request)

    assert exc.value.status_code == 403


def test_extract_client_ip_prefers_cf_connecting_ip_for_real_cloudflare_proxy():
    request = create_mock_webhook_request(
        client_ip="172.19.0.3",
        headers={
            "X-Real-IP": "104.21.87.138",
            "X-Forwarded-For": "104.21.87.138",
            "CF-Connecting-IP": "91.108.5.53",
        },
    )

    result = extract_client_ip(request)

    assert result.value == "91.108.5.53"
    assert result.source == "CF-Connecting-IP"


def test_extract_client_ip_ignores_spoofed_cf_header_on_dns_only_subdomain():
    request = create_mock_webhook_request(
        client_ip="172.19.0.3",
        headers={
            "X-Real-IP": "203.0.113.10",
            "X-Forwarded-For": "203.0.113.10",
            "CF-Connecting-IP": "91.108.5.53",
        },
    )

    result = extract_client_ip(request)

    assert result.value == "203.0.113.10"
    assert result.source == "X-Real-IP"


def test_ip_middlewares_use_same_safe_real_ip_extraction():
    request = create_mock_webhook_request(
        client_ip="172.19.0.3",
        headers={
            "X-Real-IP": "104.21.87.138",
            "X-Forwarded-For": "104.21.87.138",
            "CF-Connecting-IP": "91.108.5.53",
        },
    )

    ip_ban = IPBanMiddleware(app=MagicMock())
    security_monitor = SecurityMonitorMiddleware(app=MagicMock())

    assert ip_ban._get_client_ip(request) == "91.108.5.53"
    assert security_monitor._get_client_ip(request) == "91.108.5.53"


def test_rate_limiter_uses_safe_real_ip_extraction():
    request = create_mock_webhook_request(
        client_ip="172.19.0.3",
        headers={
            "X-Real-IP": "104.21.87.138",
            "X-Forwarded-For": "104.21.87.138",
            "CF-Connecting-IP": "91.108.5.53",
        },
    )

    assert get_rate_limit_ip(request) == "91.108.5.53"
