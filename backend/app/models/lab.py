from sqlalchemy import Text, DateTime, Integer, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .submission import Submission

class Lab(Base, TimestampMixin):
    __tablename__ = "labs"
    __table_args__ = (
        CheckConstraint("length(title) <= 200", name="ck_labs_title_len"),
        CheckConstraint("length(s3_key) <= 500", name="ck_labs_s3_key_len"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    s3_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Файл задания
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    max_grade: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    
    # Автор лабы (преподаватель) - опционально, если нужно знать кто создал
    # teacher_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Связи
    submissions: Mapped[list["Submission"]] = relationship(back_populates="lab", cascade="all, delete-orphan")