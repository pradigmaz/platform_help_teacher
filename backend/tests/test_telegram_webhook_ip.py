from unittest.mock import Mock

import pytest
from fastapi import HTTPException, Request

from app.api.deps import verify_telegram_ip


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
