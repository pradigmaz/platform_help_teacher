import enum
from datetime import date
from sqlalchemy import ForeignKey, Date, Enum as SAEnum, UniqueConstraint, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from typing import Optional, TYPE_CHECKING

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .lesson import Lesson


class AttendanceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    EXCUSED = "EXCUSED"


class LessonType(str, enum.Enum):
    """Тип занятия для посещаемости"""
    LECTURE = "lecture"
    PRACTICE = "practice"
    LAB = "lab"


class Attendance(Base, TimestampMixin):
    __tablename__ = "attendance"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    group_id: Mapped[UUID] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[AttendanceStatus] = mapped_column(
        SAEnum(AttendanceStatus, name="attendance_status_enum", create_constraint=False, native_enum=False),
        default=AttendanceStatus.ABSENT, 
        nullable=False
    )
    
    # Новые поля для связи с расписанием
    lesson_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("lessons.id", ondelete="SET NULL"), 
        nullable=True
    )
    lesson_type: Mapped[Optional[LessonType]] = mapped_column(
        SAEnum(LessonType, name="attendancelessontype", create_constraint=False, native_enum=False),
        nullable=True
    )
    lesson_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Номер пары
    subgroup: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Подгруппа

    # Связи
    student: Mapped["User"] = relationship(foreign_keys=[student_id])
    creator: Mapped["User"] = relationship(foreign_keys=[created_by])
    group: Mapped["Group"] = relationship()
    lesson: Mapped[Optional["Lesson"]] = relationship()

    __table_args__ = (
        UniqueConstraint('student_id', 'date', 'lesson_number', name='uq_attendance_student_date_lesson'),
        Index('idx_attendance_group_date', 'group_id', 'date'),
        Index('idx_attendance_lesson', 'lesson_id'),
    )