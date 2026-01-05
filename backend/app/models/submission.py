from sqlalchemy import String, Integer, ForeignKey, Text, Boolean, CheckConstraint, Enum as SAEnum, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from uuid import UUID, uuid4
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import date
import enum

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .lab import Lab

class SubmissionStatus(str, enum.Enum):
    NEW = "NEW"
    IN_REVIEW = "IN_REVIEW"
    REQ_CHANGES = "REQ_CHANGES"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

class Submission(Base, TimestampMixin):
    __tablename__ = "submissions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lab_id: Mapped[UUID] = mapped_column(ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)
    
    status: Mapped[SubmissionStatus] = mapped_column(SAEnum(SubmissionStatus), default=SubmissionStatus.NEW, nullable=False)
    
    # Обновленная логика: файл может отсутствовать, если это ручная оценка
    s3_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    grade: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Привязка к занятию
    lesson_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    lesson_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # История изменений (JSON)
    history: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)

    # Связи
    user: Mapped["User"] = relationship(back_populates="submissions")
    lab: Mapped["Lab"] = relationship(back_populates="submissions")

    __table_args__ = (
        # Constraint: Либо это ручная оценка, либо должен быть файл
        CheckConstraint('(is_manual IS TRUE) OR (s3_key IS NOT NULL)', name='check_file_required_if_not_manual'),
        # Constraint: Оценка от 0 до 100
        CheckConstraint('(grade IS NULL) OR (grade >= 0 AND grade <= 100)', name='check_grade_range'),
    )