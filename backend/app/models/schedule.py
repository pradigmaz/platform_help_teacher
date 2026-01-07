"""
Модель расписания занятий.
"""
import enum
from datetime import date
from typing import Optional, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import ForeignKey, Date, Enum as SAEnum, String, Integer, Boolean, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .group import Group
    from .user import User
    from .subject import Subject


class DayOfWeek(str, enum.Enum):
    """День недели"""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"


class LessonType(str, enum.Enum):
    """Тип занятия"""
    LECTURE = "lecture"      # Лекция
    PRACTICE = "practice"    # Практика
    LAB = "lab"              # Лабораторная


class WeekParity(str, enum.Enum):
    """Чётность недели"""
    ODD = "odd"      # Нечётная
    EVEN = "even"    # Чётная


class ScheduleItem(Base, TimestampMixin):
    """
    Элемент расписания (одна пара).
    Описывает регулярное занятие в расписании группы.
    """
    __tablename__ = "schedule_items"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    group_id: Mapped[UUID] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    # Когда
    day_of_week: Mapped[DayOfWeek] = mapped_column(
        SAEnum(DayOfWeek, name="dayofweek", create_constraint=False, native_enum=False),
        nullable=False
    )
    lesson_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-8
    
    # Что
    lesson_type: Mapped[LessonType] = mapped_column(
        SAEnum(LessonType, name="lessontype", create_constraint=False, native_enum=False),
        nullable=False
    )
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Legacy string
    subject_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    room: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Кто ведёт
    teacher_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True
    )
    
    # Период действия
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # null = бессрочно
    
    # Чётность недели (null = каждую неделю)
    week_parity: Mapped[Optional[WeekParity]] = mapped_column(
        SAEnum(WeekParity, name="weekparity", create_constraint=False, native_enum=False),
        nullable=True
    )
    
    # Подгруппа (null = вся группа)
    subgroup: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1 или 2
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    group: Mapped["Group"] = relationship()
    teacher: Mapped[Optional["User"]] = relationship()
    subject_ref: Mapped[Optional["Subject"]] = relationship()

    __table_args__ = (
        Index('idx_schedule_group_day', 'group_id', 'day_of_week'),
        CheckConstraint('lesson_number >= 1 AND lesson_number <= 8', name='ck_schedule_lesson_number'),
        CheckConstraint('subgroup IS NULL OR subgroup IN (1, 2)', name='ck_schedule_subgroup'),
    )
