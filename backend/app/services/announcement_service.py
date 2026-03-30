"""Сервис для работы с объявлениями и рассылкой уведомлений."""

import logging
from typing import TypeAlias

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.announcement import Announcement
from app.models.notification_settings import NotificationSettings
from app.models.user import User, UserRole
from app.services.notification_service import _send_telegram, _send_vk

logger = logging.getLogger(__name__)
NotificationRecipient: TypeAlias = tuple[User, NotificationSettings | None]


async def get_students_for_notification(db: AsyncSession) -> list[NotificationRecipient]:
    """Получить студентов с настройками уведомлений."""
    result = await db.execute(
        select(User, NotificationSettings)
        .outerjoin(NotificationSettings, User.id == NotificationSettings.user_id)
        .where(User.role == UserRole.STUDENT)
    )
    return [(user, settings) for user, settings in result.all()]


async def send_announcement_to_students(db: AsyncSession, announcement: Announcement) -> dict:
    """
    Отправить объявление студентам через ботов.
    Учитывает настройки каждого студента.
    """
    stats = {"telegram_sent": 0, "vk_sent": 0, "skipped": 0, "errors": 0}

    message = format_announcement_message(announcement)
    students_data = await get_students_for_notification(db)

    for user, settings in students_data:
        # Если нет настроек — используем дефолты (боты выключены)
        if not settings:
            stats["skipped"] += 1
            continue

        # Проверяем, включены ли уведомления об объявлениях
        if not settings.notify_announcements:
            stats["skipped"] += 1
            continue

        # Telegram
        if settings.channel_telegram and user.telegram_id:
            try:
                if await _send_telegram(user.telegram_id, message):
                    stats["telegram_sent"] += 1
            except Exception as e:
                logger.error(f"Failed to send to telegram {user.id}: {e}")
                stats["errors"] += 1

        # VK
        if settings.channel_vk and user.vk_id:
            try:
                if await _send_vk(user.vk_id, message):
                    stats["vk_sent"] += 1
            except Exception as e:
                logger.error(f"Failed to send to vk {user.id}: {e}")
                stats["errors"] += 1

    logger.info(f"Announcement {announcement.id} sent: {stats}")
    return stats


def format_announcement_message(announcement: Announcement) -> str:
    """Форматировать объявление для отправки."""
    return f"📢 {announcement.title}\n\n{announcement.content[:1000]}"
