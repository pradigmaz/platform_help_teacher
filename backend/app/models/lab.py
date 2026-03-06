from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .lab_deadline_extension import LabDeadlineExtension
    from .lesson import Lesson
    from .subject import Subject
    from .submission import Submission


class Lab(Base, TimestampMixin):
    """
    Лабораторная/практическая работа.

    Новый формат: 4 секции (шапка, теория, практика с вариантами, контрольные вопросы).
    Выполняется в тетради, сдаётся устно преподавателю.
    """

    __tablename__ = "labs"
    __table_args__ = (
        CheckConstraint("length(title) <= 200", name="ck_labs_title_len"),
        CheckConstraint("length(s3_key) <= 500", name="ck_labs_s3_key_len"),
        CheckConstraint("number > 0", name="ck_labs_number_positive"),
        Index("idx_labs_subject_number", "subject_id", "number"),
        # uq_labs_subject_number — partial unique index, создаётся через миграцию 083
        # (UniqueConstraint не поддерживает WHERE clause в SQLAlchemy)
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Порядковый номер лабы (1, 2, 3...)
    number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Связь с предметом
    subject_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Связь с занятием из расписания (для синхронизации оценок с журналом)
    lesson_id: Mapped[UUID | None] = mapped_column(ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True)

    # === Секция 1: Шапка ===
    title: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str | None] = mapped_column(Text, nullable=True)  # Тема
    goal: Mapped[str | None] = mapped_column(Text, nullable=True)  # Цель работы
    formatting_guide: Mapped[str | None] = mapped_column(Text, nullable=True)  # Что записать в тетрадь

    # === Секция 2: Теория ===
    theory_content: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, default=None, comment="Теоретическая часть (Lexical JSON)"
    )

    # === Секция 3: Практика ===
    practice_content: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, default=None, comment="Общее задание практики (Lexical JSON)"
    )
    variants: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB, nullable=True, default=None, comment="Массив вариантов [{number, description, test_data}, ...]"
    )

    # === Секция 4: Контрольные вопросы ===
    questions: Mapped[list[Any] | None] = mapped_column(
        JSONB, nullable=True, default=None, comment="Список контрольных вопросов (str или Lexical JSON)"
    )

    # === Настройки ===
    # Дедлайны: через сколько пар (LAB) блокируется оценка
    # 1 = следующая пара, 2 = через пару, и т.д.
    deadline_5_lessons: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deadline_4_lessons: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_grade: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    is_sequential: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Требуется ли сдача предыдущей лабы для доступа"
    )

    # Legacy поля (для обратной совместимости)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    s3_key: Mapped[str | None] = mapped_column(Text, nullable=True)  # Файл задания (старый формат)

    # Публикация
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    public_code: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True, index=True)

    # Soft-delete
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Связи
    submissions: Mapped[list["Submission"]] = relationship(back_populates="lab", cascade="all, delete-orphan")
    subject: Mapped[Optional["Subject"]] = relationship()
    lesson: Mapped[Optional["Lesson"]] = relationship()
    deadline_extensions: Mapped[list["LabDeadlineExtension"]] = relationship(
        back_populates="lab", cascade="all, delete-orphan"
    )
