"""Feedback attachment model for screenshots."""

from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class FeedbackAttachment(Base):
    __tablename__ = "feedback_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    feedback_id = Column(
        UUID(as_uuid=True),
        ForeignKey("feedback.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    content_type = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    is_uploaded = Column(Boolean, default=False, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    feedback = relationship("Feedback", back_populates="attachments")
