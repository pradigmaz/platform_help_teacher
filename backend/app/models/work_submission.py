from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .work import Work


class WorkSubmission(Base, TimestampMixin):
    """Сдача универсальной работы студентом"""

    __tablename__ = "work_submissions"
    __table_args__ = (
        CheckConstraint("(is_manual IS TRUE) OR (s3_key IS NOT NULL)", name="ck_work_sub_file_required"),
        CheckConstraint("(grade IS NULL) OR (grade >= 0 AND grade <= 100)", name="ck_work_sub_grade_range"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    work_id: Mapped[UUID] = mapped_column(ForeignKey("works.id", ondelete="CASCADE"), nullable=False, index=True)

    grade: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    s3_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Связи
    user: Mapped["User"] = relationship(back_populates="work_submissions")
    work: Mapped["Work"] = relationship(back_populates="submissions")
