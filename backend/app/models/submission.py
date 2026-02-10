import enum
from datetime import date, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .lab import Lab
    from .user import User


class SubmissionStatus(str, enum.Enum):
    NEW = "NEW"  # Не начал (или работает)
    READY = "READY"  # Нажал "Готов сдать" (в очереди)
    IN_REVIEW = "IN_REVIEW"  # На проверке (legacy)
    REQ_CHANGES = "REQ_CHANGES"  # Требуются изменения (legacy)
    ACCEPTED = "ACCEPTED"  # Принято, оценка выставлена
    REJECTED = "REJECTED"  # Отклонено, нужно доработать


class Submission(Base, TimestampMixin):
    """
    Сдача лабораторной работы студентом.

    Новый flow:
    1. NEW → студент работает над лабой
    2. READY → студент нажал "Готов сдать", попал в очередь
    3. ACCEPTED → преподаватель принял работу, выставил оценку
    или REJECTED → преподаватель отклонил, нужно доработать
    """

    __tablename__ = "submissions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lab_id: Mapped[UUID] = mapped_column(ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)

    status: Mapped[SubmissionStatus] = mapped_column(
        SAEnum(SubmissionStatus), default=SubmissionStatus.NEW, nullable=False
    )

    # Номер варианта (определяется по номеру студента в списке группы)
    variant_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Обновленная логика: файл может отсутствовать, если это ручная оценка
    s3_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_manual: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    grade: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Привязка к занятию (legacy)
    lesson_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    lesson_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Временные метки нового flow
    ready_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Когда студент нажал 'Готов сдать'"
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Когда преподаватель принял работу"
    )

    # История изменений (JSON)
    history: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)

    # Soft-delete
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Когда сдача была удалена (soft-delete)"
    )

    # Связи
    user: Mapped["User"] = relationship(back_populates="submissions")
    lab: Mapped["Lab"] = relationship(back_populates="submissions")

    __table_args__ = (
        # Constraint: Либо это ручная оценка, либо должен быть файл
        CheckConstraint("(is_manual IS TRUE) OR (s3_key IS NOT NULL)", name="check_file_required_if_not_manual"),
        # Constraint: Оценка от 0 до 100
        CheckConstraint("(grade IS NULL) OR (grade >= 0 AND grade <= 100)", name="check_grade_range"),
        # Unique: один студент = одна сдача на лабу
        UniqueConstraint("user_id", "lab_id", name="uq_submission_user_lab"),
        # Index для быстрой фильтрации по статусу (очередь)
        Index("idx_submission_status", "status"),
        # Composite index для запросов очереди
        Index("idx_submission_status_ready_at", "status", "ready_at"),
    )
