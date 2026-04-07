"""Pydantic schemas for announcements."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.announcement import AnnouncementSendStatus


class AnnouncementCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    content: str = Field(..., min_length=10, max_length=50000)


class AnnouncementUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=200)
    content: str | None = Field(None, min_length=10, max_length=50000)


class AnnouncementResponse(BaseModel):
    id: UUID
    title: str
    content: str
    created_by: UUID | None = None
    author_name: str | None = None
    is_draft: bool
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnnouncementListResponse(BaseModel):
    id: UUID
    title: str
    content: str
    is_draft: bool
    published_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnnouncementDeliveryStats(BaseModel):
    telegram_sent: int = 0
    vk_sent: int = 0
    skipped: int = 0
    errors: int = 0


class AdminAnnouncementListResponse(BaseModel):
    id: UUID
    title: str
    content: str
    author_name: str | None = None
    is_draft: bool
    send_status: AnnouncementSendStatus
    published_at: datetime | None = None
    send_started_at: datetime | None = None
    sent_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    delivery_stats: AnnouncementDeliveryStats | None = None
    delivery_error: str | None = None

    model_config = {"from_attributes": True}


class AdminAnnouncementResponse(AdminAnnouncementListResponse):
    created_by: UUID | None = None
    sent_by: UUID | None = None
