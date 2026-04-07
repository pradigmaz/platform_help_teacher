"""Announcement model for changelog and notifications."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class AnnouncementSendStatus(str, enum.Enum):
    NOT_SENT = "not_sent"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"


ANNOUNCEMENT_SEND_STATUS_DB_VALUES = [status.value for status in AnnouncementSendStatus]


class Announcement(Base, TimestampMixin):
    """System announcements and changelog entries."""

    __tablename__ = "announcements"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Author
    created_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    author: Mapped["User | None"] = relationship("User", backref="announcements", foreign_keys=[created_by])

    # Publishing
    is_draft: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    # Delivery lifecycle
    send_status: Mapped[AnnouncementSendStatus] = mapped_column(
        SAEnum(
            AnnouncementSendStatus,
            name="announcement_send_status_enum",
            values_callable=lambda _: ANNOUNCEMENT_SEND_STATUS_DB_VALUES,
        ),
        default=AnnouncementSendStatus.NOT_SENT,
        nullable=False,
        index=True,
    )
    send_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    delivery_stats: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    delivery_error: Mapped[str | None] = mapped_column(Text, nullable=True)
