"""Notification settings for students."""
from uuid import uuid4

from sqlalchemy import Boolean, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class NotificationSettings(Base, TimestampMixin):
    """User notification preferences."""
    __tablename__ = "notification_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # Channels
    channel_telegram = Column(Boolean, default=False, nullable=False)
    channel_vk = Column(Boolean, default=False, nullable=False)
    channel_web = Column(Boolean, default=True, nullable=False)

    # Types (only announcements for now)
    notify_announcements = Column(Boolean, default=True, nullable=False)

    # Relationship
    user = relationship("User", backref="notification_settings")
