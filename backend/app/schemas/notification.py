"""Pydantic schemas for notification settings."""

from pydantic import BaseModel


class NotificationSettingsResponse(BaseModel):
    channel_telegram: bool
    channel_vk: bool
    channel_web: bool
    notify_announcements: bool

    model_config = {"from_attributes": True}


class NotificationSettingsUpdate(BaseModel):
    channel_telegram: bool | None = None
    channel_vk: bool | None = None
    channel_web: bool | None = None
    notify_announcements: bool | None = None
