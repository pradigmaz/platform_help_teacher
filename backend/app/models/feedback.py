"""Feedback model for bug reports and suggestions."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.feedback_attachment import FeedbackAttachment
    from app.models.user import User


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

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    type: Mapped[FeedbackType] = mapped_column(
        Enum(FeedbackType, name="feedbacktype", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[FeedbackStatus] = mapped_column(
        Enum(FeedbackStatus, name="feedbackstatus", create_type=False, values_callable=lambda x: [e.value for e in x]),
        default=FeedbackStatus.NEW,
        nullable=False,
    )

    # User who submitted
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user: Mapped["User"] = relationship("User", backref="feedbacks")

    # Admin response
    admin_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Attachments
    attachments: Mapped[list["FeedbackAttachment"]] = relationship(
        "FeedbackAttachment",
        back_populates="feedback",
        cascade="all, delete-orphan",
    )
