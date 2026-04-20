import asyncio
from unittest.mock import AsyncMock

import pytest

from app.services.bot import webhook_startup


@pytest.mark.asyncio
async def test_register_telegram_webhook_returns_quickly_on_timeout(monkeypatch):
    async def slow_set_webhook(**kwargs):
        await asyncio.sleep(0.01)

    monkeypatch.setattr(webhook_startup.settings, "TELEGRAM_WEBHOOK_URL", "https://example.test", raising=False)
    monkeypatch.setattr(webhook_startup.settings, "TELEGRAM_WEBHOOK_SECRET", "secret", raising=False)
    monkeypatch.setattr(webhook_startup, "TELEGRAM_SEND_TIMEOUT_SECONDS", 0.001)
    monkeypatch.setattr(webhook_startup.bot, "set_webhook", slow_set_webhook)

    await webhook_startup.register_telegram_webhook()


@pytest.mark.asyncio
async def test_register_telegram_webhook_skips_when_url_missing(monkeypatch):
    set_webhook = AsyncMock()

    monkeypatch.setattr(webhook_startup.settings, "TELEGRAM_WEBHOOK_URL", None, raising=False)
    monkeypatch.setattr(webhook_startup.bot, "set_webhook", set_webhook)

    await webhook_startup.register_telegram_webhook()

    set_webhook.assert_not_awaited()
