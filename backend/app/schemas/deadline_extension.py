"""
Схемы для продления дедлайнов лабораторных.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DeadlineExtensionCreate(BaseModel):
    """Создание продления дедлайна."""
    lab_id: UUID
    group_id: UUID
    bonus_lessons: int = Field(default=1, ge=1, le=10, description="Количество дополнительных пар")
    reason: Optional[str] = Field(default=None, max_length=500)
    expires_at: Optional[datetime] = None


class DeadlineExtensionUpdate(BaseModel):
    """Обновление продления дедлайна."""
    bonus_lessons: Optional[int] = Field(default=None, ge=1, le=10)
    reason: Optional[str] = Field(default=None, max_length=500)
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class DeadlineExtensionResponse(BaseModel):
    """Ответ с информацией о продлении."""
    id: UUID
    lab_id: UUID
    group_id: UUID
    bonus_lessons: int
    reason: Optional[str]
    expires_at: Optional[datetime]
    is_active: bool
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    # Дополнительные поля для отображения
    lab_number: Optional[int] = None
    lab_title: Optional[str] = None
    group_name: Optional[str] = None
    creator_name: Optional[str] = None

    model_config = {"from_attributes": True}


class DeadlineExtensionListResponse(BaseModel):
    """Список продлений."""
    items: list[DeadlineExtensionResponse]
    total: int
