"""Notification settings for students."""

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class NotificationSettings(Base, TimestampMixin):
    """User notification preferences."""

    __tablename__ = "notification_settings"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    # Channels
    channel_telegram: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    channel_vk: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    channel_web: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Types (only announcements for now)
    notify_announcements: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationship
    user: Mapped["User"] = relationship("User", backref="notification_settings")
