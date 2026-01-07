"""
Модель оценки за занятие (лабу/практику).
"""
from typing import Optional, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import ForeignKey, String, Integer, UniqueConstraint, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

# Константы для валидации оценок
MIN_GRADE = 2
MAX_GRADE = 5

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .lesson import Lesson
    from .user import User


class LessonGrade(Base, TimestampMixin):
    """
    Оценка за занятие (лабу/практику).
    
    Отдельно от Work/WorkSubmission, т.к. это оценки за обычные лабы/практики,
    а не за "большие" работы (курсовые, контрольные).
    
    work_number может отличаться от lesson.work_number - студент может сдать
    другую работу (долг) на текущем занятии.
    """
    __tablename__ = "lesson_grades"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    lesson_id: Mapped[UUID] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    student_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Какую работу сдаёт (может != lesson.work_number для долгов)
    work_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Оценка 2-5
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    
    comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    created_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    lesson: Mapped["Lesson"] = relationship(back_populates="grades")
    student: Mapped["User"] = relationship(foreign_keys=[student_id])
    creator: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by])

    __table_args__ = (
        UniqueConstraint('lesson_id', 'student_id', 'work_number', 
                        name='uq_lesson_grade_student_lesson_work'),
        Index('idx_lesson_grades_lesson_student', 'lesson_id', 'student_id'),
        Index('idx_lesson_grades_work_number', 'work_number'),
        CheckConstraint(f'grade >= {MIN_GRADE} AND grade <= {MAX_GRADE}', 
                       name='ck_lesson_grade_range'),
    )
