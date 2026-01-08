"""
Модель аудита действий студентов.
"""
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, Dict, Any, List

from sqlalchemy import String, ForeignKey, Text, SmallInteger, Integer, Index, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class StudentAuditLog(Base):
    """
    Лог действий студентов.
    Партиционируется по месяцам для производительности.
    """
    __tablename__ = "student_audit_log"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Идентификация пользователя
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    actor_role: Mapped[str] = mapped_column(String(20), nullable=False, default="anonymous", index=True)
    
    # Действие
    action_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    
    # HTTP контекст
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    query_params: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    request_body: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    response_status: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Клиент
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False, index=True)
    ip_forwarded: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    # Fingerprint и дополнительные данные
    fingerprint: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    __table_args__ = (
        Index('idx_audit_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_user_time', 'user_id', 'created_at'),
        # Партиционирование добавляется в миграции
    )
