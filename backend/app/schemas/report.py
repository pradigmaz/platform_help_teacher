"""
Pydantic схемы для публичных отчётов.
Включает схемы для создания, обновления, публичного доступа и экспорта.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from app.schemas.user import PublicTeacherContacts


class ReportType(str, Enum):
    """Типы отчётов."""
    FULL = "full"
    ATTESTATION_ONLY = "attestation_only"
    ATTENDANCE_ONLY = "attendance_only"


# ============== Admin Schemas ==============

class ReportCreate(BaseModel):
    """Схема создания отчёта."""
    group_id: UUID
    report_type: ReportType = ReportType.FULL
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="Срок действия в днях (null = бессрочно)")
    pin_code: Optional[str] = Field(None, min_length=4, max_length=6, pattern=r'^\d+$', description="PIN-код (4-6 цифр)")
    show_names: bool = True
    show_grades: bool = True
    show_attendance: bool = True
    show_notes: bool = True
    show_rating: bool = True


class ReportUpdate(BaseModel):
    """Схема обновления отчёта."""
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="Срок действия в днях")
    pin_code: Optional[str] = Field(None, min_length=4, max_length=6, pattern=r'^\d+$', description="Новый PIN-код")
    remove_pin: bool = Field(False, description="Удалить PIN-защиту")
    show_names: Optional[bool] = None
    show_grades: Optional[bool] = None
    show_attendance: Optional[bool] = None
    show_notes: Optional[bool] = None
    show_rating: Optional[bool] = None
    is_active: Optional[bool] = None


class ReportResponse(BaseModel):
    """Схема ответа с данными отчёта."""
    id: UUID
    code: str
    group_id: UUID
    group_code: str
    group_name: Optional[str] = None
    report_type: ReportType
    expires_at: Optional[datetime]
    has_pin: bool
    show_names: bool
    show_grades: bool
    show_attendance: bool
    show_notes: bool
    show_rating: bool
    is_active: bool
    views_count: int
    last_viewed_at: Optional[datetime]
    created_at: datetime
    url: str = Field(description="Полная ссылка на отчёт")

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Схема списка отчётов."""
    reports: List[ReportResponse]
    total: int


# ============== Public Report Schemas ==============

class PublicStudentData(BaseModel):
    """Данные студента для публичного отчёта."""
    id: UUID
    name: Optional[str] = Field(None, description="ФИО (null если show_names=False)")
    
    # Аттестация (если show_grades)
    total_score: Optional[float] = None
    lab_score: Optional[float] = None
    attendance_score: Optional[float] = None
    activity_score: Optional[float] = None
    grade: Optional[str] = None
    is_passing: Optional[bool] = None
    
    # Посещаемость (если show_attendance)
    attendance_rate: Optional[float] = Field(None, description="Процент посещаемости")
    present_count: Optional[int] = None
    absent_count: Optional[int] = None
    late_count: Optional[int] = None
    excused_count: Optional[int] = None
    
    # Лабораторные
    labs_completed: Optional[int] = None
    labs_total: Optional[int] = None
    
    # Флаги
    needs_attention: bool = Field(False, description="Требует внимания (не сдаёт)")
    
    # Заметки (если show_notes)
    notes: Optional[List[str]] = None


class AttendanceDistribution(BaseModel):
    """Распределение посещаемости для графика."""
    present: int = 0
    late: int = 0
    excused: int = 0
    absent: int = 0


class LabProgress(BaseModel):
    """Прогресс сдачи лабораторных для графика."""
    lab_name: str
    completed_count: int
    total_students: int
    completion_rate: float


class PublicReportData(BaseModel):
    """Данные для публичной страницы отчёта группы."""
    group_code: str
    group_name: Optional[str] = None
    subject_name: Optional[str] = None
    teacher_name: str
    report_type: ReportType
    generated_at: datetime
    
    # Контакты преподавателя (отфильтрованные по visibility: report или both)
    teacher_contacts: Optional[PublicTeacherContacts] = None
    
    # Настройки видимости
    show_names: bool
    show_grades: bool
    show_attendance: bool
    show_notes: bool
    show_rating: bool
    
    # Статистика (если show_grades)
    total_students: int
    passing_students: Optional[int] = None
    failing_students: Optional[int] = None
    average_score: Optional[float] = None
    
    # Данные студентов
    students: List[PublicStudentData]
    
    # Графики (если соответствующие данные включены)
    attendance_distribution: Optional[AttendanceDistribution] = None
    lab_progress: Optional[List[LabProgress]] = None
    
    # Распределение оценок
    grade_distribution: Optional[Dict[str, int]] = None


# ============== Student Detail Schemas ==============

class AttendanceRecord(BaseModel):
    """Запись о посещении."""
    date: datetime
    status: str = Field(description="present/late/excused/absent")
    lesson_topic: Optional[str] = None


class LabSubmission(BaseModel):
    """Информация о сдаче лабораторной."""
    lab_id: UUID
    lab_name: str
    lab_number: int
    grade: Optional[float] = None
    max_grade: float
    submitted_at: Optional[datetime] = None
    is_submitted: bool
    is_late: bool = False


class ActivityRecord(BaseModel):
    """Запись об активности."""
    date: datetime
    description: str
    points: float


class StudentDetailData(BaseModel):
    """Детальные данные студента для публичного отчёта."""
    id: UUID
    name: Optional[str] = None
    group_code: str
    
    # Аттестация
    total_score: Optional[float] = None
    lab_score: Optional[float] = None
    attendance_score: Optional[float] = None
    activity_score: Optional[float] = None
    grade: Optional[str] = None
    is_passing: Optional[bool] = None
    max_points: int = 100
    min_passing_points: int = 61
    
    # Сравнение с группой
    group_average_score: Optional[float] = None
    rank_in_group: Optional[int] = None
    total_in_group: Optional[int] = None
    
    # Посещаемость
    attendance_rate: Optional[float] = None
    attendance_history: Optional[List[AttendanceRecord]] = None
    present_count: Optional[int] = None
    absent_count: Optional[int] = None
    late_count: Optional[int] = None
    excused_count: Optional[int] = None
    total_lessons: Optional[int] = None
    
    # Лабораторные
    labs_completed: Optional[int] = None
    labs_total: Optional[int] = None
    lab_submissions: Optional[List[LabSubmission]] = None
    
    # Активность
    activity_records: Optional[List[ActivityRecord]] = None
    total_activity_points: Optional[float] = None
    
    # Заметки
    notes: Optional[List[str]] = None
    
    # Рекомендации (для не сдающих)
    recommendations: Optional[List[str]] = None
    
    # Флаги
    needs_attention: bool = False


# ============== PIN Verification ==============

class PinVerifyRequest(BaseModel):
    """Запрос проверки PIN-кода."""
    pin: str = Field(..., min_length=4, max_length=6, pattern=r'^\d+$')


class PinVerifyResponse(BaseModel):
    """Ответ проверки PIN-кода."""
    success: bool
    message: Optional[str] = None
    attempts_left: Optional[int] = None
    retry_after: Optional[int] = Field(None, description="Секунды до следующей попытки")


# ============== Export Schemas ==============

class ExportResponse(BaseModel):
    """Ответ с данными экспорта."""
    filename: str
    content_type: str
    generated_at: datetime
    report_code: str
    group_code: str
    teacher_name: str
    total_students: int


class ReportViewStats(BaseModel):
    """Статистика просмотров отчёта."""
    total_views: int
    unique_ips: int
    last_viewed_at: Optional[datetime]
    views_by_date: Dict[str, int] = Field(default_factory=dict, description="Просмотры по датам")


class ReportViewRecord(BaseModel):
    """Запись о просмотре отчёта."""
    viewed_at: datetime
    ip_address: str
    user_agent: Optional[str] = None

    class Config:
        from_attributes = True


class ReportViewsResponse(BaseModel):
    """Ответ со статистикой просмотров."""
    report_id: UUID
    stats: ReportViewStats
    recent_views: List[ReportViewRecord] = Field(default_factory=list, description="Последние 50 просмотров")
