"""
Backup notification service.
Sends backup files to admin via Telegram/VK.
"""
import asyncio
import logging
from pathlib import Path
from typing import Optional
from aiogram import Bot
from aiogram.types import FSInputFile
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.core.config import settings

logger = logging.getLogger(__name__)


class BackupNotificationService:
    """Service for sending backup notifications and files."""
    
    def __init__(self):
        self._bot: Optional[Bot] = None
        self._vk_session = None
        self._vk_api = None
        self._vk_upload = None
    
    @property
    def bot(self) -> Bot:
        """Lazy init Telegram bot."""
        if self._bot is None:
            self._bot = Bot(
                token=settings.TELEGRAM_BOT_TOKEN,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
            )
        return self._bot
    
    def _init_vk(self) -> bool:
        """Lazy init VK API."""
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
        except Exception as e:
            logger.error(f"Failed to init VK API: {e}")
            return False
    
    async def send_backup_to_admin(
        self,
        file_path: Path,
        backup_name: str,
        size: int,
        admin_telegram_id: Optional[int] = None,
    ) -> bool:
        """
        Send encrypted backup file to admin via Telegram.
        
        Args:
            file_path: Path to encrypted backup file
            backup_name: Name of the backup
            size: File size in bytes
            admin_telegram_id: Telegram ID to send to (defaults to FIRST_SUPERUSER_ID)
        
        Returns:
            True if sent successfully
        """
        telegram_id = admin_telegram_id or settings.FIRST_SUPERUSER_ID
        
        if not telegram_id:
            logger.warning("No admin Telegram ID configured for backup notification")
            return False
        
        try:
            size_kb = size / 1024
            caption = (
                f"🔐 <b>Резервная копия БД</b>\n\n"
                f"📦 <code>{backup_name}</code>\n"
                f"📊 Размер: {size_kb:.1f} KB\n\n"
                f"⚠️ Файл зашифрован AES-256-GCM"
            )
            
            document = FSInputFile(file_path, filename=backup_name)
            await self.bot.send_document(
                chat_id=telegram_id,
                document=document,
                caption=caption,
            )
            
            logger.info(f"Backup sent to admin {telegram_id}: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send backup to admin: {e}")
            return False
    
    async def send_backup_to_vk(
        self,
        file_path: Path,
        backup_name: str,
        size: int,
        admin_vk_id: Optional[int] = None,
    ) -> bool:
        """
        Send encrypted backup file to admin via VK.
        
        Args:
            file_path: Path to encrypted backup file
            backup_name: Name of the backup
            size: File size in bytes
            admin_vk_id: VK ID to send to
        
        Returns:
            True if sent successfully
        """
        if not admin_vk_id:
            logger.warning("No admin VK ID provided for backup notification")
            return False
        
        if not self._init_vk():
            logger.warning("VK bot not configured")
            return False
        
        try:
            import vk_api.utils
            
            size_kb = size / 1024
            caption = (
                f"🔐 Резервная копия БД\n\n"
                f"📦 {backup_name}\n"
                f"📊 Размер: {size_kb:.1f} KB\n\n"
                f"⚠️ Файл зашифрован AES-256-GCM"
            )
            
            loop = asyncio.get_event_loop()
            
            # VkUpload.document_message is sync, run in executor
            doc = await loop.run_in_executor(
                None,
                lambda: self._vk_upload.document_message(
                    str(file_path),
                    title=backup_name,
                    peer_id=admin_vk_id
                )
            )
            
            attachment = f"doc{doc['doc']['owner_id']}_{doc['doc']['id']}"
            
            await loop.run_in_executor(
                None,
                lambda: self._vk_api.messages.send(
                    peer_id=admin_vk_id,
                    message=caption,
                    attachment=attachment,
                    random_id=vk_api.utils.get_random_id()
                )
            )
            
            logger.info(f"Backup sent to VK admin {admin_vk_id}: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send backup to VK: {e}")
            return False
    
    async def notify_backup_success(
        self,
        backup_name: str,
        size: int,
        admin_telegram_id: Optional[int] = None,
    ) -> bool:
        """Send success notification without file."""
        telegram_id = admin_telegram_id or settings.FIRST_SUPERUSER_ID
        
        if not telegram_id:
            return False
        
        try:
            size_kb = size / 1024
            text = (
                f"✅ <b>Бэкап создан успешно</b>\n\n"
                f"📦 <code>{backup_name}</code>\n"
                f"📊 Размер: {size_kb:.1f} KB"
            )
            
            await self.bot.send_message(chat_id=telegram_id, text=text)
            return True
            
        except Exception as e:
            logger.error(f"Failed to send backup notification: {e}")
            return False
    
    async def notify_backup_failure(
        self,
        error: str,
        admin_telegram_id: Optional[int] = None,
        traceback_text: Optional[str] = None,
    ) -> bool:
        """Send failure notification with optional log file."""
        telegram_id = admin_telegram_id or settings.FIRST_SUPERUSER_ID
        
        if not telegram_id:
            return False
        
        try:
            text = (
                f"❌ <b>Ошибка создания бэкапа</b>\n\n"
                f"<code>{error[:500]}</code>"
            )
            
            # If traceback provided, send as file
            if traceback_text:
                import tempfile
                from aiogram.types import FSInputFile
                from datetime import datetime
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                with tempfile.NamedTemporaryFile(
                    mode='w',
                    suffix='.log',
                    prefix=f'backup_error_{timestamp}_',
                    delete=False,
                    encoding='utf-8'
                ) as f:
                    f.write(f"Backup Error Log\n")
                    f.write(f"================\n")
                    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    f.write(f"Error: {error}\n\n")
                    f.write(f"Full Traceback:\n")
                    f.write(f"{traceback_text}\n")
                    log_path = f.name
                
                document = FSInputFile(log_path, filename=f"backup_error_{timestamp}.log")
                await self.bot.send_document(
                    chat_id=telegram_id,
                    document=document,
                    caption=text,
                )
                
                # Cleanup temp file
                import os
                os.unlink(log_path)
            else:
                await self.bot.send_message(chat_id=telegram_id, text=text)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send failure notification: {e}")
            return False
    
    async def close(self):
        """Close bot session."""
        if self._bot:
            await self._bot.session.close()
            self._bot = None


# Singleton instance
_notification_service: Optional[BackupNotificationService] = None


def get_notification_service() -> BackupNotificationService:
    """Get or create notification service singleton."""
    global _notification_service
    if _notification_service is None:
        _notification_service = BackupNotificationService()
    return _notification_service
