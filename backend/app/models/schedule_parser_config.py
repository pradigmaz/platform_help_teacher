"""
Модель настроек автопарсера расписания
"""
from uuid import UUID, uuid4
from sqlalchemy import String, Boolean, Integer, ForeignKey
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
    
    # День недели (0=пн, 6=вс)
    day_of_week: Mapped[int] = mapped_column(Integer, default=6)  # воскресенье
    
    # Время запуска (HH:MM)
    run_time: Mapped[str] = mapped_column(String(5), default="20:00")
    
    # Сколько дней вперёд парсить
    parse_days_ahead: Mapped[int] = mapped_column(Integer, default=14)
    
    # Связь с преподавателем
    teacher = relationship("User", back_populates="parser_config")
