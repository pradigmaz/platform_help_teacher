from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

# Разрываем циклический импорт
if TYPE_CHECKING:
    from .group import Group
    from .lecture_image import LectureImage
    from .subject import Subject

class Lecture(Base, TimestampMixin):
    __tablename__ = "lectures"
    __table_args__ = (
        CheckConstraint("length(title) <= 300", name="ck_lectures_title_len"),
        Index(
            'idx_lectures_public_code',
            'public_code',
            unique=True,
            postgresql_where="public_code IS NOT NULL"
        ),
        Index('idx_lectures_subject_id', 'subject_id'),
        Index('idx_lectures_deleted_at', 'deleted_at'),
        Index('idx_lectures_created_by_id', 'created_by_id'),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    public_code: Mapped[str | None] = mapped_column(String(8), nullable=True, unique=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    subject_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True
    )
    # IDOR Protection: Track who created the lecture
    created_by_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    subject: Mapped[Optional["Subject"]] = relationship("Subject")

    groups: Mapped[list["Group"]] = relationship(
        secondary="lecture_groups",
        back_populates="lectures"
    )
    images: Mapped[list["LectureImage"]] = relationship(
        back_populates="lecture",
        cascade="all, delete-orphan"
    )
