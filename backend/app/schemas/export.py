"""Схемы для экспорта журнала."""

from datetime import date as date_type, datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ExportPeriodType(str, Enum):
    """Типы периодов для экспорта."""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    SEMESTER = "semester"
    CUSTOM = "custom"


class ExportFormat(str, Enum):
    """Форматы файлов экспорта."""

    XLSX = "xlsx"
    CSV = "csv"
    JSON = "json"


class JournalExportRequest(BaseModel):
    """Параметры запроса на экспорт журнала."""

    group_id: UUID = Field(..., description="ID группы для экспорта")
    period_type: ExportPeriodType = Field(
        default=ExportPeriodType.SEMESTER,
        description="Тип периода экспорта",
    )
    period_value: Optional[str] = Field(
        default=None,
        description="Значение периода: day='2025-01-22', week='2025-W04', month='2025-01', custom='2025-01-01:2025-01-31'",
    )
    format: ExportFormat = Field(
        default=ExportFormat.XLSX,
        description="Формат выходного файла",
    )
    include_attendance: bool = Field(
        default=True,
        description="Включить данные посещаемости",
    )
    include_grades: bool = Field(
        default=True,
        description="Включить данные оценок",
    )

    @field_validator("period_value")
    @classmethod
    def validate_period_value(cls, v: Optional[str], info) -> Optional[str]:
        """Валидация: period_value обязателен для всех типов кроме SEMESTER."""
        period_type = info.data.get("period_type")
        if period_type and period_type != ExportPeriodType.SEMESTER and not v:
            raise ValueError(
                f"period_value обязателен для period_type={period_type}"
            )
        return v


class JournalExportMeta(BaseModel):
    """Метаданные экспортируемого файла."""

    group_code: str = Field(..., description="Код группы")
    group_name: Optional[str] = Field(default=None, description="Название группы")
    period_start: date_type = Field(..., description="Начало периода")
    period_end: date_type = Field(..., description="Конец периода")
    generated_at: datetime = Field(..., description="Время генерации файла")
    total_students: int = Field(..., description="Количество студентов")
    total_lessons: int = Field(..., description="Количество занятий")


class AttendanceExportRow(BaseModel):
    """Строка посещаемости студента для экспорта."""

    student_id: UUID = Field(..., description="ID студента")
    student_name: str = Field(..., description="ФИО студента")
    subgroup: Optional[int] = Field(default=None, description="Номер подгруппы")
    attendance_by_date: Dict[str, str] = Field(
        default_factory=dict,
        description="Посещаемость по датам: дата → статус (PRESENT/ABSENT/LATE/EXCUSED)",
    )
    stats: Dict[str, int] = Field(
        default_factory=dict,
        description="Статистика: present_count, absent_count, late_count, excused_count, total",
    )
    attendance_rate: float = Field(..., description="Процент посещаемости (0-100)")


class GradeExportRow(BaseModel):
    """Строка оценок студента для экспорта."""

    student_id: UUID = Field(..., description="ID студента")
    student_name: str = Field(..., description="ФИО студента")
    subgroup: Optional[int] = Field(default=None, description="Номер подгруппы")
    grades_by_work: Dict[str, Optional[int]] = Field(
        default_factory=dict,
        description="Оценки по работам: work_key → оценка (2-5 или None)",
    )
    average_grade: Optional[float] = Field(
        default=None,
        description="Средний балл",
    )
    grades_count: int = Field(default=0, description="Количество оценок")


class LessonExportColumn(BaseModel):
    """Колонка занятия для экспорта."""

    lesson_id: UUID = Field(..., description="ID занятия")
    date: date_type = Field(..., description="Дата занятия")
    lesson_number: int = Field(..., description="Номер пары")
    lesson_type: str = Field(..., description="Тип занятия (лекция/практика/лаба)")
    topic: Optional[str] = Field(default=None, description="Тема занятия")
    work_number: Optional[int] = Field(default=None, description="Номер работы")
    subgroup: Optional[int] = Field(default=None, description="Подгруппа")


class JournalExportData(BaseModel):
    """Полные данные журнала для экспорта."""

    meta: JournalExportMeta = Field(..., description="Метаданные экспорта")
    lessons: List[LessonExportColumn] = Field(
        default_factory=list,
        description="Список занятий (колонки)",
    )
    attendance_rows: List[AttendanceExportRow] = Field(
        default_factory=list,
        description="Строки посещаемости студентов",
    )
    grade_rows: List[GradeExportRow] = Field(
        default_factory=list,
        description="Строки оценок студентов",
    )
