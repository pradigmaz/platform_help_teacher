from sqlalchemy import Text, DateTime, Integer, ForeignKey, CheckConstraint, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .submission import Submission
    from .subject import Subject
    from .lesson import Lesson


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
        Index('idx_labs_subject_number', 'subject_id', 'number'),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    
    # Порядковый номер лабы (1, 2, 3...)
    number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # Связь с предметом
    subject_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Связь с занятием из расписания (для синхронизации оценок с журналом)
    lesson_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("lessons.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # === Секция 1: Шапка ===
    title: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Тема
    goal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Цель работы
    formatting_guide: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Что записать в тетрадь
    
    # === Секция 2: Теория ===
    theory_content: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, default=None,
        comment="Теоретическая часть (Lexical JSON)"
    )
    
    # === Секция 3: Практика ===
    practice_content: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, default=None,
        comment="Общее задание практики (Lexical JSON)"
    )
    variants: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB, nullable=True, default=None,
        comment="Массив вариантов [{number, description, test_data}, ...]"
    )
    
    # === Секция 4: Контрольные вопросы ===
    questions: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, default=None,
        comment="Список контрольных вопросов"
    )
    
    # === Настройки ===
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    max_grade: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    is_sequential: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
        comment="Требуется ли сдача предыдущей лабы для доступа"
    )
    
    # Legacy поля (для обратной совместимости)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    s3_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Файл задания (старый формат)
    
    # Публикация
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    public_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True, unique=True, index=True)
    
    # Soft-delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Связи
    submissions: Mapped[List["Submission"]] = relationship(back_populates="lab", cascade="all, delete-orphan")
    subject: Mapped[Optional["Subject"]] = relationship()
    lesson: Mapped[Optional["Lesson"]] = relationship()