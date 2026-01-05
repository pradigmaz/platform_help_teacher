"""
Модель публичного отчёта по группе.
Позволяет генерировать уникальные ссылки для кураторов и родителей.
"""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from uuid import uuid4
from enum import Enum

from sqlalchemy import String, Text, Boolean, DateTime, Integer, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .group import Group
    from .user import User
    from .report_view import ReportView


class ReportType(str, Enum):
    """Типы отчётов."""
    FULL = "full"
    ATTESTATION_ONLY = "attestation_only"
    ATTENDANCE_ONLY = "attendance_only"


class GroupReport(Base, TimestampMixin):
    """
    Публичный отчёт по группе.
    Доступен по уникальному коду без авторизации (опционально с PIN).
    """
    __tablename__ = "group_reports"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Связи
    group_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("groups.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    created_by: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Уникальный код (8 символов)
    code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False, index=True)
    
    # Настройки
    report_type: Mapped[str] = mapped_column(String(20), default=ReportType.FULL.value, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    pin_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    
    # Видимость
    show_names: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_grades: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_attendance: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_notes: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_rating: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Статус
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Статистика
    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_viewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    group: Mapped["Group"] = relationship("Group", lazy="joined")
    creator: Mapped["User"] = relationship("User", lazy="joined")
    views: Mapped[List["ReportView"]] = relationship(
        "ReportView", 
        back_populates="report",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_group_reports_group', 'group_id'),
        Index('idx_group_reports_creator', 'created_by'),
    )
