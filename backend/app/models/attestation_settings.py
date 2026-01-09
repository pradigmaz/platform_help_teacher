"""
Модель глобальных настроек аттестации.
Система автобалансировки: веса + количество работ → автоматический расчёт баллов.

Фиксированные константы университета:
- 1-я аттестация: макс 35 баллов
- 2-я аттестация: макс 70 баллов (накопительно)
- Коэффициенты: grade_5 = 1.0 (фикс), grade_2 = 0.0 (фикс)
"""
from datetime import date, timedelta
from sqlalchemy import Integer, Float, Boolean, Date, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid4
from enum import Enum
from typing import Optional, Tuple
from .base import Base, TimestampMixin


# Константы недель аттестации по регламенту
FIRST_ATTESTATION_WEEK = 8
SECOND_ATTESTATION_WEEK = 14

# Фиксированные коэффициенты (не хранятся в БД)
GRADE_5_COEF = 1.0  # Фиксировано
GRADE_2_COEF = 0.0  # Фиксировано (работа не засчитана)


class AttestationType(str, Enum):
    """Тип аттестации"""
    FIRST = "first"   # 1-я аттестация (макс 35 баллов)
    SECOND = "second" # 2-я аттестация (макс 70 баллов, накопительно)

    @property
    def number(self) -> int:
        return 1 if self == AttestationType.FIRST else 2
    
    @property
    def max_points(self) -> int:
        return 35 if self == AttestationType.FIRST else 70


class AttestationSettings(Base, TimestampMixin):
    """
    Настройки автобалансировки аттестации.
    
    Препод задаёт:
    - Веса компонентов (лабы, посещаемость, резерв активности)
    - Количество работ для каждой аттестации
    - Коэффициенты оценок 4 и 3 (5=1.0 и 2=0.0 фиксированы)
    
    Система автоматически рассчитывает баллы за каждую работу.
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
    
    # === ВЕСА КОМПОНЕНТОВ (сумма = 100%) ===
    labs_weight: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)
    attendance_weight: Mapped[float] = mapped_column(Float, default=20.0, nullable=False)
    activity_reserve: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    
    # === КОЛИЧЕСТВО РАБОТ ===
    labs_count_first: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    labs_count_second: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    
    # === КОЭФФИЦИЕНТЫ ОЦЕНОК (grade_5=1.0 и grade_2=0.0 фиксированы) ===
    grade_4_coef: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    grade_3_coef: Mapped[float] = mapped_column(Float, default=0.4, nullable=False)
    
    # === ПОСЕЩАЕМОСТЬ ===
    late_coef: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    
    # === ДЕДЛАЙНЫ ===
    late_max_grade: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    very_late_max_grade: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    late_threshold_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    
    # === ОПЦИОНАЛЬНЫЕ КОМПОНЕНТЫ ===
    # Самостоятельные работы
    self_works_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    self_works_weight: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    self_works_count: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    
    # Коллоквиум
    colloquium_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    colloquium_weight: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    colloquium_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # === АКТИВНОСТЬ ===
    activity_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # === ПЕРИОДЫ ===
    period_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, default=None)
    period_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, default=None)
    semester_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, default=None)
    
    # === МЕТОДЫ РАСЧЁТА ===
    
    def get_grade_coef(self, grade: int) -> float:
        """Коэффициент для оценки (5=1.0, 4=настр., 3=настр., 2=0.0)"""
        return {
            5: GRADE_5_COEF,
            4: self.grade_4_coef,
            3: self.grade_3_coef,
            2: GRADE_2_COEF
        }.get(grade, 0.0)
    
    def get_labs_count(self) -> int:
        """Количество лаб для текущего типа аттестации"""
        if self.attestation_type == AttestationType.FIRST:
            return self.labs_count_first
        return self.labs_count_first + self.labs_count_second
    
    def get_max_component_points(self, weight: float) -> float:
        """Максимум баллов для компонента = max_attestation * (weight / 100)"""
        max_att = self.attestation_type.max_points
        return max_att * (weight / 100)
    
    def get_points_per_work(self, weight: float, work_count: int) -> float:
        """Баллы за одну работу на 5 = max_component / work_count"""
        if work_count <= 0:
            return 0.0
        return self.get_max_component_points(weight) / work_count
    
    def calculate_work_points(self, grade: int, weight: float, work_count: int) -> float:
        """Баллы за работу = points_per_work * grade_coef"""
        return self.get_points_per_work(weight, work_count) * self.get_grade_coef(grade)
    
    # === СТАТИЧЕСКИЕ МЕТОДЫ ===
    
    @staticmethod
    def get_max_points(attestation_type: AttestationType) -> int:
        """Максимальные баллы по уставу университета"""
        return attestation_type.max_points
    
    @staticmethod
    def get_min_passing_points(attestation_type: AttestationType) -> int:
        """Минимальные баллы для зачёта"""
        return 20 if attestation_type == AttestationType.FIRST else 40
    
    @staticmethod
    def get_grade_scale(attestation_type: AttestationType) -> dict:
        """Фиксированная шкала оценок университета"""
        if attestation_type == AttestationType.FIRST:
            return {"неуд": (0, 19.99), "уд": (20, 25), "хор": (26, 30), "отл": (31, 35)}
        return {"неуд": (0, 39.99), "уд": (40, 50), "хор": (51, 60), "отл": (61, 70)}
    
    def validate_weights(self) -> bool:
        """Проверка суммы весов = 100%"""
        total = self.labs_weight + self.attendance_weight + self.activity_reserve
        if self.self_works_enabled:
            total += self.self_works_weight
        if self.colloquium_enabled:
            total += self.colloquium_weight
        return abs(total - 100.0) < 0.01

    @staticmethod
    def calculate_attestation_period(
        semester_start: date, 
        attestation_type: AttestationType
    ) -> Tuple[date, date]:
        """Вычисляет период аттестации"""
        if attestation_type == AttestationType.FIRST:
            return (semester_start, semester_start + timedelta(weeks=FIRST_ATTESTATION_WEEK))
        return (
            semester_start + timedelta(weeks=FIRST_ATTESTATION_WEEK),
            semester_start + timedelta(weeks=SECOND_ATTESTATION_WEEK)
        )
