"""
Модель просмотра отчёта для аудита.
Логирует каждый просмотр публичного отчёта.
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func

from .base import Base

if TYPE_CHECKING:
    from .group_report import GroupReport


class ReportView(Base):
    """
    Запись о просмотре отчёта.
    Используется для аудита и статистики.
    """
    __tablename__ = "report_views"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Связь с отчётом
    report_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("group_reports.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Данные просмотра
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)  # IPv6 max length
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    # Relationship
    report: Mapped["GroupReport"] = relationship("GroupReport", back_populates="views")

    __table_args__ = (
        Index('idx_report_views_report', 'report_id'),
        Index('idx_report_views_viewed_at', 'viewed_at'),
    )
