"""
Pydantic схемы для rate limit warnings.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from .constants import WarningLevel


class WarningResponse(BaseModel):
    """Ответ с информацией о предупреждении."""
    level: WarningLevel
    message: str
    ban_until: Optional[datetime] = None
    violation_count: int


class WarningRecord(BaseModel):
    """Запись предупреждения из БД."""
    id: UUID
    user_id: Optional[UUID]
    user_name: Optional[str] = None
    ip_address: str
    warning_level: str
    violation_count: int
    message: Optional[str]
    ban_until: Optional[datetime]
    unbanned_at: Optional[datetime]
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
    ban_until: Optional[datetime] = None
    warning_level: Optional[WarningLevel] = None
    message: Optional[str] = None
    can_unban: bool = True
