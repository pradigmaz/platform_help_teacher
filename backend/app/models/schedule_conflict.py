"""
Модель конфликтов парсинга расписания
"""
import enum
from uuid import UUID, uuid4
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base, TimestampMixin


class ConflictType(str, enum.Enum):
    """Тип конфликта"""
    CHANGED = "changed"   # Занятие изменилось
    DELETED = "deleted"   # Занятие исчезло из расписания


class ScheduleConflict(Base, TimestampMixin):
    """Конфликт при парсинге расписания"""
    __tablename__ = "schedule_conflicts"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    
    # Связь с занятием
    lesson_id: Mapped[UUID] = mapped_column(ForeignKey("lessons.id"))
    
    # Тип конфликта (string для простоты)
    conflict_type: Mapped[str] = mapped_column(String(20))
    
    # Старые данные (JSON)
    old_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Новые данные (JSON, null для deleted)
    new_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    # Разрешён ли конфликт
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Как разрешён (accept/reject)
    resolution: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # Связь с занятием
    lesson = relationship("Lesson", back_populates="conflicts")
