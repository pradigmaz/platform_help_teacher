"""Student notifications endpoints."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.crud.crud_announcement import crud_announcement
from app.crud.crud_notification_settings import crud_notification_settings
from app.models.user import User
from app.schemas.announcement import AnnouncementListResponse
from app.schemas.notification import NotificationSettingsResponse, NotificationSettingsUpdate

router = APIRouter()


@router.get("/notifications/settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationSettingsResponse:
    """Получить настройки уведомлений."""
    settings = await crud_notification_settings.get_or_create(db, current_user.id)
    return NotificationSettingsResponse.model_validate(settings)


@router.put("/notifications/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    request: Request,
    data: NotificationSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationSettingsResponse:
    """Обновить настройки уведомлений."""
    settings = await crud_notification_settings.get_or_create(db, current_user.id)

    # Проверяем, что каналы привязаны
    if data.channel_telegram and not current_user.telegram_id:
        data.channel_telegram = False
    if data.channel_vk and not current_user.vk_id:
        data.channel_vk = False

    settings = await crud_notification_settings.update(
        db,
        settings,
        channel_telegram=data.channel_telegram,
        channel_vk=data.channel_vk,
        channel_web=data.channel_web,
        notify_announcements=data.notify_announcements,
    )
    return NotificationSettingsResponse.model_validate(settings)


@router.get("/announcements", response_model=list[AnnouncementListResponse])
async def get_announcements(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AnnouncementListResponse]:
    """Получить опубликованные объявления."""
    announcements = await crud_announcement.get_published(db, skip=skip, limit=limit)
    return [AnnouncementListResponse.model_validate(a) for a in announcements]
