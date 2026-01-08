"""
SQLAlchemy модели для rate limit warnings.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class RateLimitWarning(Base):
    """Запись о предупреждении/бане за превышение лимита."""
    
    __tablename__ = "rate_limit_warnings"
    
    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Идентификация
    user_id: Optional[UUID] = Column(
        PGUUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    ip_address: str = Column(String(45), nullable=False, index=True)
    fingerprint_hash: Optional[str] = Column(String(64), nullable=True, index=True)
    
    # Детали
    warning_level: str = Column(String(20), nullable=False)  # WarningLevel enum value
    violation_count: int = Column(Integer, nullable=False)  # Сколько 429 было
    message: str = Column(Text, nullable=True)
    
    # Бан
    ban_until: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    unbanned_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    unbanned_by: Optional[UUID] = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    unban_reason: Optional[str] = Column(Text, nullable=True)
    
    # Уведомления
    admin_notified: bool = Column(default=False)
    
    # Timestamps
    created_at: datetime = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], lazy="selectin")
    
    __table_args__ = (
        Index("idx_rlw_user_created", "user_id", "created_at"),
        Index("idx_rlw_ip_created", "ip_address", "created_at"),
        Index("idx_rlw_active_bans", "ban_until", postgresql_where="ban_until IS NOT NULL AND unbanned_at IS NULL"),
    )
