"""
Модель глобальных настроек аттестации.
Хранит конфигурацию расчёта баллов для первой и второй аттестации.
Настройки применяются ко всем группам и предметам.
"""
from datetime import date, timedelta
from sqlalchemy import String, Integer, Float, Boolean, Date, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid4
from enum import Enum
from typing import Dict, Any, Optional, Tuple
from .base import Base, TimestampMixin


# Константы недель аттестации по регламенту
FIRST_ATTESTATION_WEEK = 8   # 1-я аттестация на 8-й неделе
SECOND_ATTESTATION_WEEK = 14  # 2-я аттестация на 14-й неделе


class AttestationType(str, Enum):
    """Тип аттестации"""
    FIRST = "first"   # 1-я аттестация (7-я неделя, макс 35 баллов)
    SECOND = "second" # 2-я аттестация (13-я неделя, макс 70 баллов)

    @property
    def number(self) -> int:
        return 1 if self == AttestationType.FIRST else 2


class AttestationSettings(Base, TimestampMixin):
    """
    Глобальные настройки расчёта баллов для аттестации.
    Применяются ко всем группам и предметам.
    
    Фиксированные ограничения университета:
    - 1-я аттестация: макс 35 баллов, мин 20 для зачёта
    - 2-я аттестация: макс 70 баллов, мин 40 для зачёта
    
    Настраиваемые параметры:
    - Веса компонентов (лабы, посещаемость, активность)
    - Коэффициенты штрафов за просрочку
    - Баллы за статусы посещаемости
    """
    __tablename__ = "attestation_settings"
    
    __table_args__ = (
        UniqueConstraint('attestation_type', name='uq_attestation_type'),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    attestation_type: Mapped[AttestationType] = mapped_column(
        SQLEnum(AttestationType, name='attestationtype', create_constraint=False, native_enum=False),
        nullable=False,
        unique=True
    )
    
    # Веса компонентов (должны суммироваться в 100)
    labs_weight: Mapped[float] = mapped_column(Float, default=60.0, nullable=False)
    attendance_weight: Mapped[float] = mapped_column(Float, default=20.0, nullable=False)
    activity_weight: Mapped[float] = mapped_column(Float, default=20.0, nullable=False)
    
    # Настройки лабораторных работ
    required_labs_count: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    bonus_per_extra_lab: Mapped[float] = mapped_column(Float, default=0.4, nullable=False)
    
    # Коэффициенты штрафов за просрочку (Requirements 1.7, 1.8, 1.9)
    soft_deadline_penalty: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    hard_deadline_penalty: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    soft_deadline_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    
    # Настройки посещаемости - баллы за статусы
    present_points: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    late_points: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    excused_points: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    absent_points: Mapped[float] = mapped_column(Float, default=-0.1, nullable=False)
    
    # Настройки активности (Requirements 1.10)
    activity_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    participation_points: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    
    # Период аттестации (для фильтрации посещаемости)
    period_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, default=None)
    period_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, default=None)
    
    # Дата начала семестра (для автовычисления периодов)
    semester_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, default=None)
    
    # Новая гибкая конфигурация компонентов (JSON)
    components_config: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, 
        nullable=True,
        default=None,
        comment="Гибкая конфигурация компонентов аттестации"
    )
    
    # Фиксированные константы университета (не хранятся в БД)
    @staticmethod
    def get_max_points(attestation_type: AttestationType) -> int:
        """Максимальные баллы по уставу университета"""
        return 35 if attestation_type == AttestationType.FIRST else 70
    
    @staticmethod
    def get_min_passing_points(attestation_type: AttestationType) -> int:
        """Минимальные баллы для зачёта по уставу университета"""
        return 20 if attestation_type == AttestationType.FIRST else 40
    
    @staticmethod
    def get_grade_scale(attestation_type: AttestationType) -> dict:
        """
        Фиксированная шкала оценок университета.
        Возвращает словарь с границами для каждой оценки.
        """
        if attestation_type == AttestationType.FIRST:
            return {
                "неуд": (0, 19.99),
                "уд": (20, 25),
                "хор": (26, 30),
                "отл": (31, 35)
            }
        else:
            return {
                "неуд": (0, 39.99),
                "уд": (40, 50),
                "хор": (51, 60),
                "отл": (61, 70)
            }
    
    def validate_weights(self) -> bool:
        """Проверка, что веса компонентов суммируются в 100%"""
        total = self.labs_weight + self.attendance_weight + self.activity_weight
        return abs(total - 100.0) < 0.01

    @staticmethod
    def calculate_attestation_period(
        semester_start: date, 
        attestation_type: 'AttestationType'
    ) -> Tuple[date, date]:
        """
        Вычисляет период аттестации на основе даты начала семестра.
        
        По регламенту:
        - 1-я аттестация: недели 1-8 (баллы накапливаются, макс 35)
        - 2-я аттестация: недели 9-14 (баллы накапливаются, макс 70)
        
        Returns:
            Tuple[date, date]: (начало периода, конец периода)
        """
        if attestation_type == AttestationType.FIRST:
            # Период 1-й аттестации: начало семестра → конец 8-й недели
            start = semester_start
            end = semester_start + timedelta(weeks=FIRST_ATTESTATION_WEEK)
        else:
            # Период 2-й аттестации: конец 8-й недели → конец 14-й недели
            start = semester_start + timedelta(weeks=FIRST_ATTESTATION_WEEK)
            end = semester_start + timedelta(weeks=SECOND_ATTESTATION_WEEK)
        return (start, end)
