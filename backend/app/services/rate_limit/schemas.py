"""
Pydantic схемы для rate limit warnings.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from .constants import WarningLevel


class WarningResponse(BaseModel):
    """Ответ с информацией о предупреждении."""

    level: WarningLevel
    message: str
    ban_until: datetime | None = None
    violation_count: int


class WarningRecord(BaseModel):
    """Запись предупреждения из БД."""

    id: UUID
    user_id: UUID | None
    user_name: str | None = None
    ip_address: str
    warning_level: str
    violation_count: int
    message: str | None
    ban_until: datetime | None
    unbanned_at: datetime | None
    admin_notified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WarningListResponse(BaseModel):
    """Список предупреждений."""

    items: list[WarningRecord]
    total: int


class UnbanRequest(BaseModel):
    """Запрос на разбан."""

    reason: str


class UnbanResponse(BaseModel):
    """Ответ на разбан."""

    success: bool
    message: str
    warning_id: UUID


class ActiveBanInfo(BaseModel):
    """Информация об активном бане."""

    is_banned: bool
    ban_until: datetime | None = None
    warning_level: WarningLevel | None = None
    message: str | None = None
    can_unban: bool = True
