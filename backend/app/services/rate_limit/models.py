"""
SQLAlchemy модели для rate limit warnings.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class RateLimitWarning(Base):
    """Запись о предупреждении/бане за превышение лимита."""

    __tablename__ = "rate_limit_warnings"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Идентификация
    user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False, index=True)
    fingerprint_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # Детали
    warning_level: Mapped[str] = mapped_column(String(20), nullable=False)  # WarningLevel enum value
    violation_count: Mapped[int] = mapped_column(Integer, nullable=False)  # Сколько 429 было
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Бан
    ban_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    unbanned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    unbanned_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    unban_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Уведомления
    admin_notified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    user: Mapped["User | None"] = relationship("User", foreign_keys=[user_id], lazy="selectin")

    __table_args__ = (
        Index("idx_rlw_user_created", "user_id", "created_at"),
        Index("idx_rlw_ip_created", "ip_address", "created_at"),
        Index(
            "idx_rlw_active_bans",
            "ban_until",
            postgresql_where=text("ban_until IS NOT NULL AND unbanned_at IS NULL"),
        ),
    )
