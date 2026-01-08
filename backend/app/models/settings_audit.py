"""
Модель аудита изменений настроек.
Логирует все изменения настроек аттестации.
"""
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, Dict, Any

from sqlalchemy import String, ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class SettingsAuditLog(Base):
    """
    Лог изменений настроек аттестации.
    
    Хранит историю всех изменений для audit trail.
    """
    __tablename__ = "settings_audit_log"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    
    # Тип настроек (attestation, etc.)
    settings_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Тип аттестации (first/second) или другой идентификатор
    settings_key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Действие (create, update, delete)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Старые и новые значения
    old_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    new_values: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    
    # Изменённые поля
    changed_fields: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    
    # Кто изменил
    changed_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    changed_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[changed_by_id],
        lazy="selectin"
    )
    
    # IP адрес
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    
    # Время изменения
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    
    # Комментарий (опционально)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
