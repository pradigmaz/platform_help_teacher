import asyncio
import logging

from app.bots.telegram_bot import bot
from app.core.config import settings
from app.core.time_constants import TELEGRAM_SEND_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


async def register_telegram_webhook() -> None:
    if not settings.TELEGRAM_WEBHOOK_URL:
        return

    webhook_url = f"{settings.TELEGRAM_WEBHOOK_URL}/api/v1/webhooks/telegram"
    try:
        async with asyncio.timeout(TELEGRAM_SEND_TIMEOUT_SECONDS):
            await bot.set_webhook(
                url=webhook_url,
                secret_token=settings.TELEGRAM_WEBHOOK_SECRET,
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query"],
            )
        logger.info("Webhook registered successfully.")
    except TimeoutError:
        logger.error("CRITICAL: Telegram webhook registration timed out after %ss", TELEGRAM_SEND_TIMEOUT_SECONDS)
    except Exception as exc:  # pragma: no cover - exact provider failures vary
        logger.error("CRITICAL: Failed to register Telegram webhook: %s", exc, exc_info=True)


async def delete_telegram_webhook() -> None:
    try:
        async with asyncio.timeout(TELEGRAM_SEND_TIMEOUT_SECONDS):
            await bot.delete_webhook()
    except Exception:
        logger.warning("Failed to delete Telegram webhook during shutdown", exc_info=True)
