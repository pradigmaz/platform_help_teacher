"""
Модель связи преподаватель-предмет-группа.
"""
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import Boolean, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .group import Group
    from .subject import Subject
    from .user import User


class TeacherSubjectAssignment(Base, TimestampMixin):
    """
    Связь преподаватель-предмет-группа.

    Позволяет отслеживать:
    - Какие предметы ведёт преподаватель
    - Для каких групп
    - В какой семестр

    Примеры:
    - Миронов -> Комп. сети -> ИС-31 -> 2024-2
    - Миронов -> Информатика -> ЭК-21 -> 2024-2
    - Миронов -> Численные методы -> ИС-31 -> 2024-1
    """
    __tablename__ = "teacher_subject_assignments"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    teacher_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    subject_id: Mapped[UUID] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    group_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=True,  # null = для всех групп (лекционный поток)
        index=True
    )

    # Семестр в формате "2024-1" (год-номер)
    semester: Mapped[str | None] = mapped_column(String(10), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    teacher: Mapped["User"] = relationship()
    subject: Mapped["Subject"] = relationship(back_populates="teacher_assignments")
    group: Mapped[Optional["Group"]] = relationship()

    __table_args__ = (
        UniqueConstraint(
            'teacher_id', 'subject_id', 'group_id', 'semester',
            name='uq_teacher_subject_group_semester'
        ),
        Index('idx_tsa_teacher_semester', 'teacher_id', 'semester'),
    )
