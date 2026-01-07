"""
Модель настроек автопарсера расписания
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy import String, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class ScheduleParserConfig(Base, TimestampMixin):
    """Настройки автоматического парсинга расписания"""
    __tablename__ = "schedule_parser_configs"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    
    # Связь с преподавателем (владелец настроек)
    teacher_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    
    # Имя преподавателя для парсинга (может отличаться от full_name)
    teacher_name: Mapped[str] = mapped_column(String(100))
    
    # Включён ли автопарсинг
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Дни недели для запуска (0=пн, 6=вс)
    days_of_week: Mapped[List[int]] = mapped_column(ARRAY(Integer), default=[6])
    
    # Время запуска (HH:MM)
    run_time: Mapped[str] = mapped_column(String(5), default="20:00")
    
    # Сколько дней вперёд парсить
    parse_days_ahead: Mapped[int] = mapped_column(Integer, default=14)
    
    # Время последнего запуска (для предотвращения дублей)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Связь с преподавателем
    teacher = relationship("User", back_populates="parser_config")
