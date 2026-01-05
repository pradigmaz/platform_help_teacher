from sqlalchemy import String, Integer, ForeignKey, Text, Boolean, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID, uuid4
from typing import Optional, TYPE_CHECKING

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .work import Work


class WorkSubmission(Base, TimestampMixin):
    """Сдача универсальной работы студентом"""
    __tablename__ = "work_submissions"
    __table_args__ = (
        CheckConstraint(
            "(is_manual IS TRUE) OR (s3_key IS NOT NULL)",
            name="ck_work_sub_file_required"
        ),
        CheckConstraint(
            "(grade IS NULL) OR (grade >= 0 AND grade <= 100)",
            name="ck_work_sub_grade_range"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    work_id: Mapped[UUID] = mapped_column(
        ForeignKey("works.id", ondelete="CASCADE"), nullable=False, index=True
    )

    grade: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    s3_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Связи
    user: Mapped["User"] = relationship(back_populates="work_submissions")
    work: Mapped["Work"] = relationship(back_populates="submissions")
