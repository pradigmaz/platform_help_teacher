"""
Модель конкретного занятия (инстанс из расписания).
"""
from datetime import date
from typing import Optional, List, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import ForeignKey, Date, String, Boolean, Integer, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import Base, TimestampMixin
from .schedule import LessonType
from sqlalchemy import Enum as SAEnum

if TYPE_CHECKING:
    from .group import Group
    from .schedule import ScheduleItem
    from .work import Work
    from .subject import Subject
    from .lesson_grade import LessonGrade
    from .schedule_conflict import ScheduleConflict


class Lesson(Base, TimestampMixin):
    """
    Конкретное занятие (инстанс из расписания).
    Создаётся автоматически из ScheduleItem или вручную.
    """
    __tablename__ = "lessons"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Связь с расписанием (null если создано вручную)
    schedule_item_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("schedule_items.id", ondelete="SET NULL"),
        nullable=True
    )
    
    group_id: Mapped[UUID] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Связь с предметом
    subject_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Когда
    date: Mapped[date] = mapped_column(Date, nullable=False)
    lesson_number: Mapped[int] = mapped_column(Integer, nullable=False)  # Номер пары
    
    # Что
    lesson_type: Mapped[LessonType] = mapped_column(
        SAEnum(LessonType, name="lessontype", create_constraint=False, native_enum=False),
        nullable=False
    )
    topic: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Номер лабы/практики (1, 2, 3...)
    work_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Тип контрольной на лекции (quiz/selfwork)
    lecture_work_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Связь с работой (если на этом занятии была контрольная/лаба)
    work_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("works.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Подгруппа (null = вся группа)
    subgroup: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Отмена
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Отпустил раньше
    ended_early: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    schedule_item: Mapped[Optional["ScheduleItem"]] = relationship()
    group: Mapped["Group"] = relationship()
    work: Mapped[Optional["Work"]] = relationship()
    subject: Mapped[Optional["Subject"]] = relationship()
    grades: Mapped[List["LessonGrade"]] = relationship(back_populates="lesson")
    conflicts: Mapped[List["ScheduleConflict"]] = relationship(back_populates="lesson")

    __table_args__ = (
        Index('idx_lessons_group_date', 'group_id', 'date'),
        Index('idx_lessons_date', 'date'),
        CheckConstraint('lesson_number >= 1 AND lesson_number <= 8', name='ck_lesson_lesson_number'),
        CheckConstraint('subgroup IS NULL OR subgroup IN (1, 2)', name='ck_lesson_subgroup'),
    )
