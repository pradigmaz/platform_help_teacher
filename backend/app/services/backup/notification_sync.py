"""
Synchronous backup notifications for Celery workers.
"""

import logging
from pathlib import Path

import requests  # type: ignore[import-untyped]

from app.core.config import settings
from app.core.time_constants import BACKUP_UPLOAD_TIMEOUT_SECONDS, TELEGRAM_NOTIFICATION_TIMEOUT_SECONDS

from .notification import NotificationResult, resolve_telegram_id
from .notification_templates import build_backup_caption, build_recovery_code_message

logger = logging.getLogger(__name__)


def send_backup_to_admin_sync(
    file_path: Path,
    backup_name: str,
    size: int,
    recovery_code: str | None = None,
    admin_telegram_id: int | None = None,
) -> NotificationResult:
    telegram_id = resolve_telegram_id(admin_telegram_id)
    if not telegram_id or not settings.TELEGRAM_BOT_TOKEN:
        error = "No admin Telegram ID or bot token configured"
        logger.warning(error)
        return NotificationResult(success=False, error=error)

    try:
        with open(file_path, "rb") as file_handle:
            response = requests.post(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendDocument",
                data={
                    "chat_id": telegram_id,
                    "caption": build_backup_caption(backup_name, size / 1024),
                    "parse_mode": "HTML",
                },
                files={"document": (backup_name, file_handle)},
                timeout=BACKUP_UPLOAD_TIMEOUT_SECONDS,
            )
        if response.status_code != 200:
            error = f"Failed to send backup: {response.text}"
            logger.error(error)
            return NotificationResult(success=False, error=error)

        recovery_error = _send_recovery_code_sync(telegram_id, backup_name, recovery_code)
        logger.info("Backup sent to admin %s: %s", telegram_id, backup_name)
        return NotificationResult(success=True, error=recovery_error)
    except Exception as exc:
        error = f"Failed to send backup to admin: {exc}"
        logger.error(error)
        return NotificationResult(success=False, error=error)


def _send_recovery_code_sync(
    telegram_id: int,
    backup_name: str,
    recovery_code: str | None,
) -> str | None:
    if not recovery_code:
        return None

    response = requests.post(
        f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
        json={
            "chat_id": telegram_id,
            "text": build_recovery_code_message(backup_name, recovery_code),
            "parse_mode": "HTML",
        },
        timeout=TELEGRAM_NOTIFICATION_TIMEOUT_SECONDS,
    )
    if response.status_code == 200:
        return None
    error = f"Failed to send recovery code message: {response.text}"
    logger.warning(error)
    return error


def notify_backup_failure_sync(
    error: str,
    admin_telegram_id: int | None = None,
    traceback_text: str | None = None,
) -> NotificationResult:
    telegram_id = resolve_telegram_id(admin_telegram_id)
    if not telegram_id or not settings.TELEGRAM_BOT_TOKEN:
        return NotificationResult(success=False, error="No admin Telegram ID or bot token configured")

    message_text = f"❌ Ошибка создания бэкапа\n\n{error[:500]}"
    if traceback_text:
        message_text += "\n\nПолный traceback сохранён в логах worker."

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": telegram_id, "text": message_text},
            timeout=TELEGRAM_NOTIFICATION_TIMEOUT_SECONDS,
        )
        if response.status_code == 200:
            return NotificationResult(success=True)
        notify_error = f"Failed to send failure notification: {response.text}"
        logger.error(notify_error)
        return NotificationResult(success=False, error=notify_error)
    except Exception as exc:
        notify_error = f"Failed to send failure notification: {exc}"
        logger.error(notify_error)
        return NotificationResult(success=False, error=notify_error)
