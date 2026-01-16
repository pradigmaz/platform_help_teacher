"""Pydantic schemas for announcements."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class AnnouncementCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    content: str = Field(..., min_length=10, max_length=50000)


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    content: Optional[str] = Field(None, min_length=10, max_length=50000)


class AnnouncementResponse(BaseModel):
    id: UUID
    title: str
    content: str
    created_by: Optional[UUID] = None
    author_name: Optional[str] = None
    is_draft: bool
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnnouncementListResponse(BaseModel):
    id: UUID
    title: str
    is_draft: bool
    published_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
