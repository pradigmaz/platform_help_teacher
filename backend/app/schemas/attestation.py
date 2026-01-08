"""
Pydantic схемы для API аттестации.
Включает схемы для настроек и результатов расчёта.
"""
from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from datetime import datetime, date, timezone
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
from app.models.attestation_settings import AttestationType


# ============== Component Config Schemas ==============

class ComponentConfigBase(BaseModel):
    """Базовая конфигурация компонента"""
    enabled: bool = False
    weight: float = Field(default=0.0, ge=0, le=100)


class LabsComponentConfig(ComponentConfigBase):
    """Конфигурация лабораторных работ"""
    enabled: bool = True
    weight: float = 60.0
    grading_mode: Literal["binary", "graded"] = "graded"
    grading_scale: Literal[5, 10, 100] = 10
    required_count: int = Field(default=5, ge=0)
    bonus_per_extra: float = Field(default=0.4, ge=0)
    soft_deadline_days: int = Field(default=7, ge=0)
    soft_deadline_penalty: float = Field(default=0.7, ge=0, le=1)
    hard_deadline_penalty: float = Field(default=0.5, ge=0, le=1)


class TestsComponentConfig(ComponentConfigBase):
    """Конфигурация контрольных работ"""
    grading_scale: Literal[5, 10, 100] = 10
    count: int = Field(default=0, ge=0)


class IndependentWorksComponentConfig(ComponentConfigBase):
    """Конфигурация самостоятельных работ"""
    grading_scale: Literal[5, 10, 100] = 10
    count: int = Field(default=0, ge=0)


class ColloquiaComponentConfig(ComponentConfigBase):
    """Конфигурация коллоквиумов"""
    grading_scale: Literal[5, 10, 100] = 10
    count: int = Field(default=0, ge=0)


class AttendanceComponentConfig(ComponentConfigBase):
    """Конфигурация посещаемости"""
    enabled: bool = True
    weight: float = 20.0
    present_points: float = Field(default=1.0, ge=0)
    late_points: float = Field(default=0.5, ge=0)
    excused_points: float = Field(default=0.0, ge=0)
    absent_points: float = Field(default=-0.1, le=1)


class ActivityComponentConfig(ComponentConfigBase):
    """Конфигурация активности"""
    enabled: bool = True
    weight: float = 20.0
    participation_points: float = Field(default=0.5, ge=0)


class FinalProjectComponentConfig(ComponentConfigBase):
    """Конфигурация итогового проекта"""
    grading_scale: Literal[5, 10, 100] = 10


class ComponentsConfig(BaseModel):
    """
    Полная конфигурация всех компонентов.
    
    DEPRECATED: Эта конфигурация сохраняется в БД, но НЕ используется в расчётах.
    Калькулятор использует legacy поля (labs_weight, attendance_weight, activity_weight).
    Планируется миграция или удаление в будущих версиях.
    """
    labs: LabsComponentConfig = Field(default_factory=LabsComponentConfig)
    tests: TestsComponentConfig = Field(default_factory=TestsComponentConfig)
    independent_works: IndependentWorksComponentConfig = Field(default_factory=IndependentWorksComponentConfig)
    colloquia: ColloquiaComponentConfig = Field(default_factory=ColloquiaComponentConfig)
    attendance: AttendanceComponentConfig = Field(default_factory=AttendanceComponentConfig)
    activity: ActivityComponentConfig = Field(default_factory=ActivityComponentConfig)
    final_project: FinalProjectComponentConfig = Field(default_factory=FinalProjectComponentConfig)

    @model_validator(mode='after')
    def validate_weights_sum(self) -> 'ComponentsConfig':
        """Проверка, что веса включённых компонентов суммируются в 100%"""
        components = [self.labs, self.tests, self.independent_works, 
                      self.colloquia, self.attendance, self.activity, self.final_project]
        total = sum(c.weight for c in components if c.enabled)
        if total > 0 and abs(total - 100.0) > 0.01:
            raise ValueError(f'Веса включённых компонентов должны суммироваться в 100%, текущая сумма: {total}%')
        return self


# ============== Settings Schemas ==============

class AttestationSettingsBase(BaseModel):
    """Базовая схема настроек аттестации"""
    # Legacy поля (для обратной совместимости)
    labs_weight: float = Field(default=60.0, ge=0, le=100, description="Вес лабораторных работ (%)")
    attendance_weight: float = Field(default=20.0, ge=0, le=100, description="Вес посещаемости (%)")
    activity_weight: float = Field(default=20.0, ge=0, le=100, description="Вес активности (%)")
    
    required_labs_count: int = Field(default=5, ge=0, description="Минимальное количество лабораторных")
    bonus_per_extra_lab: float = Field(default=0.4, ge=0, description="Бонус за дополнительную лабу")
    
    soft_deadline_penalty: float = Field(default=0.7, ge=0, le=1, description="Коэффициент мягкого дедлайна")
    hard_deadline_penalty: float = Field(default=0.5, ge=0, le=1, description="Коэффициент жёсткого дедлайна")
    soft_deadline_days: int = Field(default=7, ge=0, description="Период мягкого дедлайна (дни)")
    
    present_points: float = Field(default=1.0, ge=0, description="Баллы за присутствие")
    late_points: float = Field(default=0.5, ge=0, description="Баллы за опоздание")
    excused_points: float = Field(default=0.0, ge=0, description="Баллы за уважительную причину")
    absent_points: float = Field(default=-0.1, le=0, description="Баллы за отсутствие")
    
    activity_enabled: bool = Field(default=True, description="Включить учёт активности")
    participation_points: float = Field(default=0.5, ge=0, description="Баллы за участие")
    
    # Период аттестации (для фильтрации посещаемости)
    period_start_date: Optional[date] = Field(default=None, description="Начало периода аттестации")
    period_end_date: Optional[date] = Field(default=None, description="Конец периода аттестации")
    
    # Дата начала семестра (для автовычисления периодов)
    semester_start_date: Optional[date] = Field(default=None, description="Дата начала семестра")
    
    # Новая гибкая конфигурация
    # DEPRECATED: Не используется в расчётах, только для хранения
    components_config: Optional[ComponentsConfig] = Field(
        default=None, 
        description="DEPRECATED: Гибкая конфигурация компонентов (не используется в расчётах)"
    )

    @model_validator(mode='after')
    def validate_period_dates(self) -> 'AttestationSettingsBase':
        """Проверка, что period_start_date < period_end_date"""
        if self.period_start_date and self.period_end_date:
            if self.period_start_date > self.period_end_date:
                raise ValueError('period_start_date должен быть раньше period_end_date')
        return self

    @model_validator(mode='after')
    def validate_weights_sum(self) -> 'AttestationSettingsBase':
        """Проверка, что веса компонентов суммируются в 100%"""
        total = self.labs_weight + self.attendance_weight + self.activity_weight
        if abs(total - 100.0) > 0.01:
            raise ValueError(f'Веса компонентов должны суммироваться в 100%, текущая сумма: {total}%')
        return self


class AttestationSettingsCreate(AttestationSettingsBase):
    """Схема создания настроек аттестации"""
    attestation_type: AttestationType


class AttestationSettingsUpdate(AttestationSettingsBase):
    """Схема обновления настроек аттестации"""
    attestation_type: AttestationType
    components_config: Optional[ComponentsConfig] = None


class AttestationSettingsResponse(AttestationSettingsBase):
    """Схема ответа с настройками аттестации"""
    id: UUID
    attestation_type: AttestationType
    created_at: datetime
    updated_at: datetime
    
    # Фиксированные значения университета (вычисляемые)
    max_points: int = Field(description="Максимальные баллы (фиксировано)")
    min_passing_points: int = Field(description="Минимальные баллы для зачёта (фиксировано)")
    
    # Шкала оценок
    grade_scale: Dict[str, tuple] = Field(default=None, description="Шкала оценок (неуд/уд/хор/отл)")
    
    # Вычисленные периоды на основе semester_start_date
    calculated_period_start: Optional[date] = Field(default=None, description="Вычисленное начало периода")
    calculated_period_end: Optional[date] = Field(default=None, description="Вычисленный конец периода")

    class Config:
        from_attributes = True


# ============== Calculation Result Schemas ==============

class ComponentBreakdown(BaseModel):
    """Детализация расчёта по компонентам"""
    labs_raw_score: float = Field(description="Сырой балл за лабы")
    labs_weighted_score: float = Field(description="Взвешенный балл за лабы")
    labs_count: int = Field(description="Количество сданных лаб")
    labs_required: int = Field(description="Требуемое количество лаб")
    labs_bonus: float = Field(default=0.0, description="Бонус за дополнительные лабы")
    
    attendance_raw_score: float = Field(description="Сырой балл за посещаемость")
    attendance_weighted_score: float = Field(description="Взвешенный балл за посещаемость")
    attendance_total_classes: int = Field(description="Всего занятий")
    attendance_present: int = Field(default=0, description="Присутствовал")
    attendance_late: int = Field(default=0, description="Опоздал")
    attendance_excused: int = Field(default=0, description="Уважительная причина")
    attendance_absent: int = Field(default=0, description="Отсутствовал")
    
    activity_raw_score: float = Field(default=0.0, description="Сырой балл за активность")
    activity_weighted_score: float = Field(default=0.0, description="Взвешенный балл за активность")


class AttestationResult(BaseModel):
    """Результат расчёта аттестации для студента"""
    student_id: UUID
    student_name: str
    attestation_type: AttestationType
    group_code: Optional[str] = Field(default=None, description="Код группы (для режима 'Все студенты')")
    
    total_score: float = Field(description="Итоговый балл")
    lab_score: float = Field(description="Балл за лабораторные")
    attendance_score: float = Field(description="Балл за посещаемость")
    activity_score: float = Field(description="Балл за активность")
    
    grade: str = Field(description="Оценка (неуд/уд/хор/отл)")
    is_passing: bool = Field(description="Зачёт/незачёт")
    
    max_points: int = Field(description="Максимально возможные баллы")
    min_passing_points: int = Field(description="Минимум для зачёта")
    
    components_breakdown: ComponentBreakdown = Field(description="Детализация по компонентам")


class CalculationErrorInfo(BaseModel):
    """Информация об ошибке расчёта для студента"""
    student_id: UUID
    student_name: str
    error: str


class AttestationResultResponse(AttestationResult):
    """Ответ API с результатом расчёта"""
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        from_attributes = True


class GroupAttestationResponse(BaseModel):
    """Результаты аттестации для группы"""
    group_id: Optional[UUID] = Field(default=None, description="ID группы (None для режима 'Все студенты')")
    group_code: str
    attestation_type: AttestationType
    calculated_at: datetime
    
    total_students: int
    passing_students: int
    failing_students: int
    
    grade_distribution: Dict[str, int] = Field(description="Распределение по оценкам")
    average_score: float
    
    students: List[AttestationResult]
    errors: List[CalculationErrorInfo] = Field(default_factory=list, description="Ошибки расчёта для отдельных студентов")
