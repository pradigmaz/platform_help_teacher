"""
Универсальная модель заметок.
Может быть привязана к любой сущности через entity_type + entity_id.
"""
from datetime import datetime
from typing import Optional
from uuid import uuid4
from enum import Enum

from sqlalchemy import String, Text, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from .base import Base, TimestampMixin


class EntityType(str, Enum):
    """Типы сущностей для привязки заметок."""
    LESSON = "lesson"
    STUDENT = "student"
    GROUP = "group"
    WORK = "work"
    SCHEDULE_ITEM = "schedule_item"


class NoteColor(str, Enum):
    """Цвета заметок."""
    DEFAULT = "default"
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"
    PURPLE = "purple"


class Note(Base, TimestampMixin):
    """
    Универсальная заметка.
    Привязывается к сущности через entity_type + entity_id.
    """
    __tablename__ = "notes"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Полиморфная привязка
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Контент
    content: Mapped[str] = mapped_column(Text, nullable=False)
    color: Mapped[str] = mapped_column(String(20), default=NoteColor.DEFAULT.value, nullable=False)
    
    # Флаги
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Автор (опционально, для будущего)
    author_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        Index('idx_notes_entity', 'entity_type', 'entity_id'),
    )
