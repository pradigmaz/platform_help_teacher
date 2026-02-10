"""CRUD операции для настроек уведомлений."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification_settings import NotificationSettings


class CRUDNotificationSettings:
    async def get_by_user(self, db: AsyncSession, user_id: UUID) -> NotificationSettings | None:
        """Получить настройки пользователя."""
        result = await db.execute(select(NotificationSettings).where(NotificationSettings.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_or_create(self, db: AsyncSession, user_id: UUID) -> NotificationSettings:
        """Получить или создать настройки с дефолтами."""
        settings = await self.get_by_user(db, user_id)
        if not settings:
            settings = NotificationSettings(user_id=user_id)
            db.add(settings)
            await db.commit()
            await db.refresh(settings)
        return settings

    async def update(
        self,
        db: AsyncSession,
        settings: NotificationSettings,
        channel_telegram: bool | None = None,
        channel_vk: bool | None = None,
        channel_web: bool | None = None,
        notify_announcements: bool | None = None,
    ) -> NotificationSettings:
        """Обновить настройки."""
        if channel_telegram is not None:
            settings.channel_telegram = channel_telegram
        if channel_vk is not None:
            settings.channel_vk = channel_vk
        if channel_web is not None:
            settings.channel_web = channel_web
        if notify_announcements is not None:
            settings.notify_announcements = notify_announcements

        await db.commit()
        await db.refresh(settings)
        return settings


crud_notification_settings = CRUDNotificationSettings()
