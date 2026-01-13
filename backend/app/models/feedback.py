"""Feedback model for bug reports and suggestions."""
import enum
from uuid import uuid4
from sqlalchemy import Column, String, Text, Enum, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base, TimestampMixin


class FeedbackType(str, enum.Enum):
    BUG = "bug"
    SUGGESTION = "suggestion"


class FeedbackStatus(str, enum.Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Feedback(Base, TimestampMixin):
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    type = Column(
        Enum(FeedbackType, name='feedbacktype', create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(
        Enum(FeedbackStatus, name='feedbackstatus', create_type=False, values_callable=lambda x: [e.value for e in x]),
        default=FeedbackStatus.NEW,
        nullable=False
    )
    
    # User who submitted
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", backref="feedbacks")
    
    # Admin response
    admin_response = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Attachments
    attachments = relationship("FeedbackAttachment", back_populates="feedback", cascade="all, delete-orphan")
