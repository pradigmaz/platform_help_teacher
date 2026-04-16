"""Модель глобальных настроек аттестации."""

from datetime import date, timedelta
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, Float, Integer, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin

# Константы недель аттестации по регламенту
FIRST_ATTESTATION_WEEK = 8
SECOND_ATTESTATION_WEEK = 14

# Фиксированные коэффициенты (не хранятся в БД)
GRADE_5_COEF = 1.0  # Фиксировано
GRADE_2_COEF = 0.0  # Фиксировано (работа не засчитана)


class AttestationType(str, Enum):
    """Тип аттестации"""

    FIRST = "first"  # 1-я аттестация (макс 35 баллов)
    SECOND = "second"  # 2-я аттестация (макс 70 баллов, накопительно)

    @property
    def number(self) -> int:
        return 1 if self == AttestationType.FIRST else 2

    @property
    def max_points(self) -> int:
        return 35 if self == AttestationType.FIRST else 70


class AttestationSettings(Base, TimestampMixin):
    """Настройки автобалансировки аттестации."""

    __tablename__ = "attestation_settings"

    __table_args__ = (UniqueConstraint("attestation_type", name="uq_attestation_type"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    attestation_type: Mapped[AttestationType] = mapped_column(
        SQLEnum(AttestationType, name="attestationtype", create_constraint=False, native_enum=False),
        nullable=False,
        unique=True,
    )

    # === БАЗОВЫЕ ВЕСА (сумма = 100%, без бонусной активности) ===
    labs_weight: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)
    attendance_weight: Mapped[float] = mapped_column(Float, default=30.0, nullable=False)
    activity_reserve: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)

    # === КОЛИЧЕСТВО РАБОТ ===
    labs_count_first: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    # Для SECOND хранится добавочное количество работ после FIRST.
    labs_count_second: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    # === КОЭФФИЦИЕНТЫ ОЦЕНОК (grade_5=1.0 и grade_2=0.0 фиксированы) ===
    grade_4_coef: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    grade_3_coef: Mapped[float] = mapped_column(Float, default=0.4, nullable=False)

    # === ПОСЕЩАЕМОСТЬ ===
    late_coef: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    absent_coef: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0 или отрицательный

    # === ОПЦИОНАЛЬНЫЕ БАЗОВЫЕ КОМПОНЕНТЫ ===
    self_works_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    self_works_weight: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    self_works_count: Mapped[int] = mapped_column(Integer, default=2, nullable=False)

    colloquium_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    colloquium_weight: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    colloquium_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # === БОНУСНАЯ АКТИВНОСТЬ ===
    activity_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # === ОЖИДАЕМОЕ КОЛИЧЕСТВО ЗАНЯТИЙ ===
    expected_lessons_per_week: Mapped[int] = mapped_column(Integer, default=2, nullable=False)

    # === ПЕРИОДЫ ===
    period_start_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    period_end_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    semester_start_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)

    def get_grade_coef(self, grade: int) -> float:
        """Коэффициент для оценки (5=1.0, 4=настр., 3=настр., 2=0.0)"""
        grade_4_coef = self.grade_4_coef if self.grade_4_coef is not None else 0.7
        grade_3_coef = self.grade_3_coef if self.grade_3_coef is not None else 0.4
        return {5: GRADE_5_COEF, 4: grade_4_coef, 3: grade_3_coef, 2: GRADE_2_COEF}.get(grade, 0.0)

    def get_labs_count(self) -> int:
        """Количество лаб для текущего типа аттестации"""
        if self.attestation_type == AttestationType.FIRST:
            return self.labs_count_first
        return self.labs_count_first + self.labs_count_second

    def get_min_expected_lessons(self) -> int:
        """Минимальное ожидаемое количество занятий для аттестации"""
        weeks = FIRST_ATTESTATION_WEEK if self.attestation_type == AttestationType.FIRST else SECOND_ATTESTATION_WEEK
        return self.expected_lessons_per_week * weeks

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

    @staticmethod
    def get_max_points(attestation_type: AttestationType) -> int:
        """Максимальные баллы по уставу университета"""
        return attestation_type.max_points

    @staticmethod
    def get_min_passing_points(attestation_type: AttestationType) -> int:
        """Минимальные баллы для зачёта"""
        return 20 if attestation_type == AttestationType.FIRST else 40

    def get_effective_period(self) -> tuple[date, date]:
        """
        Возвращает эффективный период аттестации.
        Если period_start/end заданы явно — возвращает их.
        Иначе вычисляет по semester_start_date и attestation_type.
        Для SECOND без semester_start_date — бросает ValueError.
        """
        if self.period_start_date and self.period_end_date:
            return self.period_start_date, self.period_end_date
        if self.semester_start_date:
            return AttestationSettings.calculate_attestation_period(self.semester_start_date, self.attestation_type)
        # FIRST без дат — допустимый fallback (скользящий период)
        if self.attestation_type == AttestationType.FIRST:
            today = date.today()
            return today - timedelta(weeks=8), today
        # SECOND без semester_start_date — ошибка конфигурации
        raise ValueError(
            "semester_start_date обязателен для расчёта периода аттестации SECOND. "
            "Укажите semester_start_date в настройках аттестации."
        )

    @staticmethod
    def get_grade_scale(attestation_type: AttestationType) -> dict:
        """
        Непрерывная шкала оценок университета.
        Интервалы: [lower, upper) для всех кроме последнего, последний [lower, upper].
        """
        if attestation_type == AttestationType.FIRST:
            return {"неуд": (0, 20), "уд": (20, 26), "хор": (26, 31), "отл": (31, 35)}
        return {"неуд": (0, 40), "уд": (40, 51), "хор": (51, 61), "отл": (61, 70)}

    def validate_weights(self) -> bool:
        """Проверка суммы базовых весов = 100% без бонусной активности."""
        total = self.labs_weight + self.attendance_weight
        if self.self_works_enabled:
            total += self.self_works_weight
        if self.colloquium_enabled:
            total += self.colloquium_weight
        return abs(total - 100.0) < 0.01

    @staticmethod
    def calculate_attestation_period(semester_start: date, attestation_type: AttestationType) -> tuple[date, date]:
        """
        Вычисляет период аттестации.

        FIRST:  (semester_start, semester_start + 8 weeks)
        SECOND: (semester_start, semester_start + 14 weeks)  — накопительно с начала семестра,
                согласуется с get_labs_count() который суммирует labs_count_first + labs_count_second.
        """
        if attestation_type == AttestationType.FIRST:
            return (semester_start, semester_start + timedelta(weeks=FIRST_ATTESTATION_WEEK))
        # SECOND — накопительный период с начала семестра (0..14 недель)
        return (semester_start, semester_start + timedelta(weeks=SECOND_ATTESTATION_WEEK))
