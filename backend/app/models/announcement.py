"""Announcement model for changelog and notifications."""
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Announcement(Base, TimestampMixin):
    """System announcements and changelog entries."""
    __tablename__ = "announcements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)

    # Author
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    author = relationship("User", backref="announcements")

    # Publishing
    is_draft = Column(Boolean, default=True, nullable=False, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
