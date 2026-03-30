"""
Asynchronous backup notifications.
"""

import asyncio
import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile

from app.core.config import settings

from .notification_templates import build_backup_caption, build_recovery_code_message

logger = logging.getLogger(__name__)


@dataclass
class NotificationResult:
    success: bool
    error: str | None = None


def resolve_telegram_id(admin_telegram_id: int | None = None) -> int | None:
    return admin_telegram_id or settings.FIRST_SUPERUSER_ID


class BackupNotificationService:
    """Service for sending backup notifications and files."""

    def __init__(self):
        self._bot: Bot | None = None
        self._vk_session = None
        self._vk_api = None
        self._vk_upload = None

    @property
    def bot(self) -> Bot:
        if self._bot is None:
            self._bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        return self._bot

    def _init_vk(self) -> bool:
        if self._vk_session is not None:
            return True
        if not settings.VK_BOT_TOKEN or not settings.VK_GROUP_ID:
            return False
        try:
            import vk_api
            from vk_api import VkUpload

            self._vk_session = vk_api.VkApi(token=settings.VK_BOT_TOKEN)
            self._vk_api = self._vk_session.get_api()
            self._vk_upload = VkUpload(self._vk_session)
            return True
        except Exception as exc:
            logger.error("Failed to init VK API: %s", exc)
            return False

    async def send_backup_to_admin(
        self,
        file_path: Path,
        backup_name: str,
        size: int,
        recovery_code: str | None = None,
        admin_telegram_id: int | None = None,
    ) -> NotificationResult:
        telegram_id = resolve_telegram_id(admin_telegram_id)
        if not telegram_id:
            error = "No admin Telegram ID configured for backup notification"
            logger.warning(error)
            return NotificationResult(success=False, error=error)
        if not settings.TELEGRAM_BOT_TOKEN:
            error = "Telegram bot token is not configured"
            logger.warning(error)
            return NotificationResult(success=False, error=error)

        try:
            await self.bot.send_document(
                chat_id=telegram_id,
                document=FSInputFile(file_path, filename=backup_name),
                caption=build_backup_caption(backup_name, size / 1024),
            )
            recovery_error = await self._send_recovery_code_message(telegram_id, backup_name, recovery_code)
            logger.info("Backup sent to admin %s: %s", telegram_id, backup_name)
            return NotificationResult(success=True, error=recovery_error)
        except Exception as exc:
            error = f"Failed to send backup to admin: {exc}"
            logger.error(error)
            return NotificationResult(success=False, error=error)

    async def send_backup_to_vk(
        self,
        file_path: Path,
        backup_name: str,
        size: int,
        admin_vk_id: int | None = None,
    ) -> bool:
        if not admin_vk_id:
            logger.warning("No admin VK ID provided for backup notification")
            return False
        if not self._init_vk():
            logger.warning("VK bot not configured")
            return False

        try:
            import vk_api.utils

            caption = (
                "🔐 Резервная копия БД\n\n"
                f"📦 {backup_name}\n"
                f"📊 Размер: {size / 1024:.1f} KB\n\n"
                "⚠️ Файл зашифрован AES-256-GCM"
            )
            loop = asyncio.get_event_loop()
            document = await loop.run_in_executor(
                None,
                lambda: self._vk_upload.document_message(str(file_path), title=backup_name, peer_id=admin_vk_id),
            )
            attachment = f"doc{document['doc']['owner_id']}_{document['doc']['id']}"
            await loop.run_in_executor(
                None,
                lambda: self._vk_api.messages.send(
                    peer_id=admin_vk_id,
                    message=caption,
                    attachment=attachment,
                    random_id=vk_api.utils.get_random_id(),
                ),
            )
            logger.info("Backup sent to VK admin %s: %s", admin_vk_id, backup_name)
            return True
        except Exception as exc:
            logger.error("Failed to send backup to VK: %s", exc)
            return False

    async def notify_backup_failure(
        self,
        error: str,
        admin_telegram_id: int | None = None,
        traceback_text: str | None = None,
    ) -> NotificationResult:
        telegram_id = resolve_telegram_id(admin_telegram_id)
        if not telegram_id:
            return NotificationResult(success=False, error="No admin Telegram ID configured for backup notification")

        try:
            text = f"❌ <b>Ошибка создания бэкапа</b>\n\n<code>{error[:500]}</code>"
            if traceback_text:
                log_file = _write_traceback_file(error, traceback_text)
                try:
                    await self.bot.send_document(
                        chat_id=telegram_id,
                        document=FSInputFile(log_file, filename=Path(log_file).name),
                        caption=text,
                    )
                finally:
                    os.unlink(log_file)
            else:
                await self.bot.send_message(chat_id=telegram_id, text=text)
            return NotificationResult(success=True)
        except Exception as exc:
            notify_error = f"Failed to send failure notification: {exc}"
            logger.error(notify_error)
            return NotificationResult(success=False, error=notify_error)

    async def close(self):
        if self._bot:
            await self._bot.session.close()
            self._bot = None

    async def _send_recovery_code_message(
        self,
        telegram_id: int,
        backup_name: str,
        recovery_code: str | None,
    ) -> str | None:
        if not recovery_code:
            return None
        try:
            await self.bot.send_message(
                chat_id=telegram_id,
                text=build_recovery_code_message(backup_name, recovery_code),
            )
            return None
        except Exception as exc:
            return f"Failed to send recovery code message: {exc}"


def _write_traceback_file(error: str, traceback_text: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".log",
        prefix=f"backup_error_{timestamp}_",
        delete=False,
        encoding="utf-8",
    ) as file_handle:
        file_handle.write("Backup Error Log\n")
        file_handle.write("================\n")
        file_handle.write(f"Timestamp: {datetime.now().isoformat()}\n")
        file_handle.write(f"Error: {error}\n\n")
        file_handle.write("Full Traceback:\n")
        file_handle.write(f"{traceback_text}\n")
        return file_handle.name


_notification_service: BackupNotificationService | None = None


def get_notification_service() -> BackupNotificationService:
    global _notification_service
    if _notification_service is None:
        _notification_service = BackupNotificationService()
    return _notification_service
