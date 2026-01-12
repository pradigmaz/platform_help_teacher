"""Pydantic schemas for feedback."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.feedback import FeedbackType, FeedbackStatus


class FeedbackCreate(BaseModel):
    type: FeedbackType
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)


class FeedbackResponse(BaseModel):
    id: UUID
    type: FeedbackType
    title: str
    description: str
    status: FeedbackStatus
    user_id: UUID
    user_name: Optional[str] = None
    admin_response: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class FeedbackUpdate(BaseModel):
    status: Optional[FeedbackStatus] = None
    admin_response: Optional[str] = Field(None, max_length=2000)
