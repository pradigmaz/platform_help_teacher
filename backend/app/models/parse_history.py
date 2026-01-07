"""
Модель истории парсинга расписания
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ParseHistory(Base):
    """История запусков парсинга"""
    __tablename__ = "parse_history"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    
    # Связь с преподавателем
    teacher_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    
    # Связь с конфигом (опционально, для ручного парсинга может быть null)
    config_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("schedule_parser_configs.id"), nullable=True
    )
    
    # Временные метки
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Статус: running, success, failed
    status: Mapped[str] = mapped_column(String(20), default="running")
    
    # Статистика
    lessons_created: Mapped[int] = mapped_column(Integer, default=0)
    lessons_updated: Mapped[int] = mapped_column(Integer, default=0)
    lessons_skipped: Mapped[int] = mapped_column(Integer, default=0)
    conflicts_created: Mapped[int] = mapped_column(Integer, default=0)
    
    # Сообщение об ошибке
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Связи
    teacher = relationship("User")
    config = relationship("ScheduleParserConfig")
