"""
Pydantic схемы для API аттестации.
Система автобалансировки: веса + количество работ → автоматический расчёт баллов.
"""
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime, date, timezone
from pydantic import BaseModel, Field, model_validator
from app.models.attestation_settings import AttestationType


# ============== Settings Schemas ==============

class AttestationSettingsBase(BaseModel):
    """Базовая схема настроек автобалансировки"""
    
    # === ВЕСА КОМПОНЕНТОВ (сумма = 100%) ===
    labs_weight: float = Field(default=70.0, ge=0, le=100, description="Вес лабораторных (%)")
    attendance_weight: float = Field(default=20.0, ge=0, le=100, description="Вес посещаемости (%)")
    activity_reserve: float = Field(default=10.0, ge=0, le=100, description="Резерв для активности (%)")
    
    # === КОЛИЧЕСТВО РАБОТ ===
    labs_count_first: int = Field(default=8, ge=1, le=20, description="Лаб для 1-й аттестации")
    labs_count_second: int = Field(default=10, ge=0, le=20, description="Доп. лаб для 2-й аттестации")
    
    # === КОЭФФИЦИЕНТЫ ОЦЕНОК (5=1.0 и 2=0.0 фиксированы) ===
    grade_4_coef: float = Field(default=0.7, ge=0, le=1, description="Коэффициент оценки 4")
    grade_3_coef: float = Field(default=0.4, ge=0, le=1, description="Коэффициент оценки 3")
    
    # === ПОСЕЩАЕМОСТЬ ===
    late_coef: float = Field(default=0.5, ge=0, le=1, description="Коэффициент опоздания")
    
    # === ДЕДЛАЙНЫ ===
    late_max_grade: int = Field(default=4, ge=2, le=5, description="Макс оценка при небольшой просрочке")
    very_late_max_grade: int = Field(default=3, ge=2, le=5, description="Макс оценка при сильной просрочке")
    late_threshold_days: int = Field(default=7, ge=0, description="Граница просрочки (дни)")
    
    # === ОПЦИОНАЛЬНЫЕ КОМПОНЕНТЫ ===
    # Самостоятельные работы
    self_works_enabled: bool = Field(default=False, description="Включить СР")
    self_works_weight: float = Field(default=0.0, ge=0, le=100, description="Вес СР (%)")
    self_works_count: int = Field(default=2, ge=1, le=10, description="Количество СР")
    
    # Коллоквиум
    colloquium_enabled: bool = Field(default=False, description="Включить коллоквиум")
    colloquium_weight: float = Field(default=0.0, ge=0, le=100, description="Вес коллоквиума (%)")
    colloquium_count: int = Field(default=1, ge=1, le=5, description="Количество коллоквиумов")
    
    # === АКТИВНОСТЬ ===
    activity_enabled: bool = Field(default=True, description="Включить активность")
    
    # === ПЕРИОДЫ ===
    period_start_date: Optional[date] = Field(default=None, description="Начало периода")
    period_end_date: Optional[date] = Field(default=None, description="Конец периода")
    semester_start_date: Optional[date] = Field(default=None, description="Начало семестра")

    @model_validator(mode='after')
    def validate_period_dates(self) -> 'AttestationSettingsBase':
        if self.period_start_date and self.period_end_date:
            if self.period_start_date > self.period_end_date:
                raise ValueError('period_start_date должен быть раньше period_end_date')
        return self

    @model_validator(mode='after')
    def validate_weights_sum(self) -> 'AttestationSettingsBase':
        total = self.labs_weight + self.attendance_weight + self.activity_reserve
        if self.self_works_enabled:
            total += self.self_works_weight
        if self.colloquium_enabled:
            total += self.colloquium_weight
        if abs(total - 100.0) > 0.01:
            raise ValueError(f'Веса должны суммироваться в 100%, текущая сумма: {total}%')
        return self


class AttestationSettingsCreate(AttestationSettingsBase):
    """Схема создания настроек"""
    attestation_type: AttestationType


class AttestationSettingsUpdate(AttestationSettingsBase):
    """Схема обновления настроек"""
    attestation_type: AttestationType


class ScorePreview(BaseModel):
    """Превью расчёта баллов (для UI)"""
    component: str = Field(description="Название компонента")
    weight: float = Field(description="Вес (%)")
    max_points: float = Field(description="Макс баллов")
    points_per_unit: float = Field(description="Баллов за единицу (на 5)")
    unit_label: str = Field(description="Единица измерения")


class AttestationSettingsResponse(AttestationSettingsBase):
    """Схема ответа с настройками"""
    id: UUID
    attestation_type: AttestationType
    created_at: datetime
    updated_at: datetime
    
    # Фиксированные значения
    max_points: int = Field(description="Максимум баллов (фикс)")
    min_passing_points: int = Field(description="Минимум для зачёта (фикс)")
    grade_scale: Dict[str, tuple] = Field(default=None, description="Шкала оценок")
    
    # Превью расчёта
    score_preview: List[ScorePreview] = Field(default=None, description="Превью баллов")
    
    # Вычисленные периоды
    calculated_period_start: Optional[date] = Field(default=None)
    calculated_period_end: Optional[date] = Field(default=None)

    class Config:
        from_attributes = True


# ============== Calculation Result Schemas ==============

class ComponentBreakdown(BaseModel):
    """Детализация расчёта по компонентам"""
    # Лабораторные
    labs_score: float = Field(description="Баллы за лабы")
    labs_count: int = Field(description="Сдано лаб")
    labs_max: float = Field(description="Макс баллов за лабы")
    
    # Посещаемость
    attendance_score: float = Field(description="Баллы за посещаемость")
    attendance_ratio: float = Field(description="Процент посещаемости")
    attendance_max: float = Field(description="Макс баллов за посещаемость")
    total_classes: int = Field(description="Всего занятий")
    present_count: int = Field(default=0)
    late_count: int = Field(default=0)
    excused_count: int = Field(default=0)
    absent_count: int = Field(default=0)
    
    # Активность
    activity_score: float = Field(default=0.0, description="Баллы за активность")
    activity_max: float = Field(description="Макс баллов (резерв)")
    bonus_blocked: bool = Field(default=False, description="Бонусы заблокированы (макс набран)")
    
    # Опциональные
    self_works_score: Optional[float] = Field(default=None)
    colloquium_score: Optional[float] = Field(default=None)


class AttestationResult(BaseModel):
    """Результат расчёта аттестации"""
    student_id: UUID
    student_name: str
    attestation_type: AttestationType
    group_code: Optional[str] = None
    
    total_score: float = Field(description="Итоговый балл")
    grade: str = Field(description="Оценка (неуд/уд/хор/отл)")
    is_passing: bool = Field(description="Зачёт")
    
    max_points: int
    min_passing_points: int
    
    breakdown: ComponentBreakdown


class CalculationErrorInfo(BaseModel):
    """Ошибка расчёта"""
    student_id: UUID
    student_name: str
    error: str


class AttestationResultResponse(AttestationResult):
    """Ответ API"""
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        from_attributes = True


class GroupAttestationResponse(BaseModel):
    """Результаты для группы"""
    group_id: Optional[UUID] = None
    group_code: str
    attestation_type: AttestationType
    calculated_at: datetime
    
    total_students: int
    passing_students: int
    failing_students: int
    
    grade_distribution: Dict[str, int]
    average_score: float
    
    students: List[AttestationResult]
    errors: List[CalculationErrorInfo] = Field(default_factory=list)
