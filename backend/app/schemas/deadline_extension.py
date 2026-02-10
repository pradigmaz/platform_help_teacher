"""
Схемы для продления дедлайнов лабораторных.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DeadlineExtensionCreate(BaseModel):
    """Создание продления дедлайна."""
    lab_id: UUID
    group_id: UUID
    bonus_lessons: int = Field(default=1, ge=1, le=10, description="Количество дополнительных пар")
    reason: str | None = Field(default=None, max_length=500)
    expires_at: datetime | None = None


class DeadlineExtensionUpdate(BaseModel):
    """Обновление продления дедлайна."""
    bonus_lessons: int | None = Field(default=None, ge=1, le=10)
    reason: str | None = Field(default=None, max_length=500)
    expires_at: datetime | None = None
    is_active: bool | None = None


class DeadlineExtensionResponse(BaseModel):
    """Ответ с информацией о продлении."""
    id: UUID
    lab_id: UUID
    group_id: UUID
    bonus_lessons: int
    reason: str | None
    expires_at: datetime | None
    is_active: bool
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime

    # Дополнительные поля для отображения
    lab_number: int | None = None
    lab_title: str | None = None
    group_name: str | None = None
    creator_name: str | None = None

    model_config = {"from_attributes": True}


class DeadlineExtensionListResponse(BaseModel):
    """Список продлений."""
    items: list[DeadlineExtensionResponse]
    total: int
