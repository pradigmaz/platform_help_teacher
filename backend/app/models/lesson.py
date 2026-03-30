"""
Модель конкретного занятия (инстанс из расписания).
"""

from datetime import date
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Index, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .schedule import LessonType

if TYPE_CHECKING:
    from .group import Group
    from .lesson_grade import LessonGrade
    from .schedule import ScheduleItem
    from .schedule_conflict import ScheduleConflict
    from .subject import Subject
    from .work import Work


class Lesson(Base, TimestampMixin):
    """
    Конкретное занятие (инстанс из расписания).
    Создаётся автоматически из ScheduleItem или вручную.
    """

    __tablename__ = "lessons"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Связь с расписанием (null если создано вручную)
    schedule_item_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("schedule_items.id", ondelete="SET NULL"), nullable=True
    )

    group_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Связь с предметом
    subject_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Когда
    date: Mapped[date] = mapped_column(Date, nullable=False)
    lesson_number: Mapped[int] = mapped_column(Integer, nullable=False)  # Номер пары

    # Что
    lesson_type: Mapped[LessonType] = mapped_column(
        SAEnum(LessonType, name="lessontype", create_constraint=False, native_enum=False), nullable=False
    )
    topic: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Номер лабы/практики (1, 2, 3...)
    work_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Тип контрольной на лекции (quiz/selfwork)
    lecture_work_type: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Связь с работой (если на этом занятии была контрольная/лаба)
    work_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("works.id", ondelete="SET NULL"), nullable=True
    )

    # Подгруппа (null = вся группа)
    subgroup: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Отмена
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cancellation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Отпустил раньше
    ended_early: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Переопределение лимита лаб за занятие (null = стандартная логика: 1 или 2 для EXCUSED)
    max_labs_override: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)

    # Relationships
    schedule_item: Mapped[Optional["ScheduleItem"]] = relationship()
    group: Mapped["Group"] = relationship()
    work: Mapped[Optional["Work"]] = relationship()
    subject: Mapped[Optional["Subject"]] = relationship()
    grades: Mapped[list["LessonGrade"]] = relationship(back_populates="lesson")
    conflicts: Mapped[list["ScheduleConflict"]] = relationship(back_populates="lesson")

    __table_args__ = (
        Index("idx_lessons_group_date", "group_id", "date"),
        Index("idx_lessons_date", "date"),
        CheckConstraint("lesson_number >= 1 AND lesson_number <= 8", name="ck_lesson_lesson_number"),
        CheckConstraint("subgroup IS NULL OR subgroup IN (1, 2)", name="ck_lesson_subgroup"),
        CheckConstraint(
            "max_labs_override IS NULL OR (max_labs_override >= 1 AND max_labs_override <= 10)",
            name="ck_lesson_max_labs_override",
        ),
    )
