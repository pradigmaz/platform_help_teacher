"""Device model for storing user device bindings."""

import uuid
from datetime import UTC, datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Device(Base):
    """Device model for tracking user devices."""

    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    fingerprint_hash = Column(String(64), nullable=False, index=True)
    device_info = Column(JSON, nullable=False, default=dict)
    first_seen = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    last_seen = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)
    is_trusted = Column(Boolean, nullable=False, default=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    # Relationships
    user = relationship("User", back_populates="devices")

    __table_args__ = (
        UniqueConstraint("user_id", "fingerprint_hash", name="uq_devices_user_fingerprint"),
        Index("ix_devices_user_trusted", "user_id", "is_trusted"),
    )

    def __repr__(self) -> str:
        return f"<Device(id={self.id}, user_id={self.user_id}, trusted={self.is_trusted})>"
