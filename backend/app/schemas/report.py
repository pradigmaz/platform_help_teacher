"""
Pydantic схемы для публичных отчётов.
Включает схемы для создания, обновления, публичного доступа и экспорта.
"""

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

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
    expires_in_days: int | None = Field(None, ge=1, le=365, description="Срок действия в днях (null = бессрочно)")
    pin_code: str | None = Field(None, min_length=4, max_length=6, pattern=r"^\d+$", description="PIN-код (4-6 цифр)")
    show_names: bool = True
    show_grades: bool = True
    show_attendance: bool = True
    show_notes: bool = True
    show_rating: bool = True


class ReportUpdate(BaseModel):
    """Схема обновления отчёта."""

    expires_in_days: int | None = Field(None, ge=1, le=365, description="Срок действия в днях")
    pin_code: str | None = Field(None, min_length=4, max_length=6, pattern=r"^\d+$", description="Новый PIN-код")
    remove_pin: bool = Field(False, description="Удалить PIN-защиту")
    show_names: bool | None = None
    show_grades: bool | None = None
    show_attendance: bool | None = None
    show_notes: bool | None = None
    show_rating: bool | None = None
    is_active: bool | None = None


class ReportResponse(BaseModel):
    """Схема ответа с данными отчёта."""

    id: UUID
    code: str
    group_id: UUID
    group_code: str
    group_name: str | None = None
    report_type: ReportType
    expires_at: datetime | None
    has_pin: bool
    show_names: bool
    show_grades: bool
    show_attendance: bool
    show_notes: bool
    show_rating: bool
    is_active: bool
    views_count: int
    last_viewed_at: datetime | None
    created_at: datetime
    url: str = Field(description="Полная ссылка на отчёт")

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Схема списка отчётов."""

    reports: list[ReportResponse]
    total: int


# ============== Public Report Schemas ==============


class PublicStudentData(BaseModel):
    """Данные студента для публичного отчёта."""

    id: UUID
    name: str | None = Field(None, description="ФИО (null если show_names=False)")
    subgroup: int | None = Field(None, description="Подгруппа (1, 2 или null)")

    # Аттестация (если show_grades)
    total_score: float | None = None
    lab_score: float | None = None
    attendance_score: float | None = None
    activity_score: float | None = None
    grade: str | None = None
    is_passing: bool | None = None

    # Посещаемость (если show_attendance)
    attendance_rate: float | None = Field(None, description="Процент посещаемости")
    present_count: int | None = None
    absent_count: int | None = None
    late_count: int | None = None
    excused_count: int | None = None

    # Лабораторные
    labs_completed: int | None = None
    labs_total: int | None = None

    # Флаги
    needs_attention: bool = Field(False, description="Требует внимания (не сдаёт)")
    calculation_error: bool = Field(False, description="Ошибка расчёта аттестации")

    # Заметки (если show_notes)
    notes: list[str] | None = None


class AttendanceDistribution(BaseModel):
    """Распределение посещаемости для графика."""

    present: int = 0
    late: int = 0
    excused: int = 0
    absent: int = 0


class DateAttendance(BaseModel):
    """Посещаемость за дату для графика динамики."""

    date: str  # ISO date string
    rate: float  # % посещаемости
    subgroup: int | None = None


class AttendanceStats(BaseModel):
    """Расширенная статистика посещаемости."""

    distribution: AttendanceDistribution
    by_subgroup: dict[str, AttendanceDistribution] = Field(default_factory=dict)
    trend: list[DateAttendance] = Field(default_factory=list)
    average_rate: float = 0.0


class LabProgress(BaseModel):
    """Прогресс сдачи лабораторных для графика."""

    lab_name: str
    completed_count: int
    total_students: int
    completion_rate: float
    subgroup: int | None = None  # None = все, 1 или 2


class TodayLessonAttendance(BaseModel):
    """Посещаемость на конкретной паре (для 'сегодня на паре')."""

    date: date
    lesson_number: int = Field(description="Номер пары (1-8)")
    lesson_type: str = Field(description="lecture/practice/lab")
    topic: str | None = None
    subgroup: int | None = Field(None, description="Подгруппа (null = лекция, вся группа)")
    present: list[str] = Field(default_factory=list, description="Присутствующие (имена или ID)")
    absent: list[str] = Field(default_factory=list, description="Отсутствующие")
    late: list[str] = Field(default_factory=list, description="Опоздавшие")
    excused: list[str] = Field(default_factory=list, description="Уважительная причина")


class LessonHistoryItem(BaseModel):
    """Элемент истории занятий."""

    date: date
    lesson_number: int = Field(description="Номер пары (1-8)")
    lesson_type: str = Field(description="lecture/practice/lab")
    topic: str | None = None
    subgroup: int | None = Field(None, description="Подгруппа (null = лекция)")
    attendance_rate: float = Field(description="Процент посещаемости")
    present_count: int = 0
    total_count: int = 0


class PublicReportData(BaseModel):
    """Данные для публичной страницы отчёта группы."""

    group_code: str
    group_name: str | None = None
    subject_name: str | None = None
    report_type: ReportType
    semester_start_date: date | None = Field(None, description="Дата начала семестра")

    # Контакты преподавателя (отфильтрованные по visibility: report или both)
    teacher_contacts: PublicTeacherContacts | None = None

    # Настройки видимости
    show_names: bool
    show_grades: bool
    show_attendance: bool
    show_notes: bool
    show_rating: bool

    # Флаг раннего семестра (не показывать предупреждения о незачёте)
    is_early_semester: bool = Field(False, description="Начало семестра - не показывать предупреждения")

    # Статистика (если show_grades)
    total_students: int
    passing_students: int | None = None
    failing_students: int | None = None
    average_score: float | None = None
    max_points: int = Field(35, description="Максимум баллов за аттестацию")
    min_passing_points: int = Field(20, description="Минимум для зачёта")

    # Шкала оценок (диапазоны баллов)
    grade_scale: dict[str, list[float]] | None = Field(
        None, description="Шкала оценок: {'неуд': [0, 19.99], 'уд': [20, 25], ...}"
    )

    # Тип аттестации
    attestation_type: str = Field("first", description="first или second")
    is_second_available: bool = Field(False, description="Доступна ли 2-я аттестация")

    # Подгруппы
    has_subgroups: bool = Field(False, description="Есть ли подгруппы в группе")

    # Данные студентов
    students: list[PublicStudentData]

    # Графики (если соответствующие данные включены)
    attendance_distribution: AttendanceDistribution | None = None
    attendance_stats: AttendanceStats | None = Field(None, description="Расширенная статистика посещаемости")
    lab_progress: list[LabProgress] | None = None
    lab_progress_by_subgroup: dict[str, list[LabProgress]] | None = Field(
        None, description="Прогресс лаб по подгруппам: all, 1, 2"
    )

    # Распределение оценок
    grade_distribution: dict[str, int] | None = None

    # Посещаемость по парам (сегодня)
    today_lessons: list[TodayLessonAttendance] | None = Field(None, description="Занятия на сегодня с посещаемостью")

    # История занятий (последние N)
    lesson_history: list[LessonHistoryItem] | None = Field(None, description="История последних занятий")


# ============== Student Detail Schemas ==============


class AttendanceRecord(BaseModel):
    """Запись о посещении."""

    date: date
    status: str = Field(description="present/late/excused/absent")
    lesson_topic: str | None = None
    lesson_number: int | None = Field(None, description="Номер пары (1-8)")
    lesson_type: str | None = Field(None, description="lecture/practice/lab")
    subgroup: int | None = Field(None, description="Подгруппа (null = вся группа)")


class LabSubmission(BaseModel):
    """Информация о сдаче лабораторной."""

    lab_id: UUID
    lab_name: str
    lab_number: int
    grade: float | None = None
    max_grade: float
    submitted_at: datetime | None = None
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
    name: str | None = None
    group_code: str

    # Аттестация
    total_score: float | None = None
    lab_score: float | None = None
    attendance_score: float | None = None
    activity_score: float | None = None
    grade: str | None = None
    is_passing: bool | None = None
    max_points: int = 100
    min_passing_points: int = 61

    # Флаг раннего семестра
    is_early_semester: bool = Field(False, description="Начало семестра - не показывать предупреждения")

    # Сравнение с группой
    group_average_score: float | None = None
    rank_in_group: int | None = None
    total_in_group: int | None = None

    # Посещаемость
    attendance_rate: float | None = None
    attendance_history: list[AttendanceRecord] | None = None
    present_count: int | None = None
    absent_count: int | None = None
    late_count: int | None = None
    excused_count: int | None = None
    total_lessons: int | None = None

    # Лабораторные
    labs_completed: int | None = None
    labs_total: int | None = None
    lab_submissions: list[LabSubmission] | None = None

    # Активность
    activity_records: list[ActivityRecord] | None = None
    total_activity_points: float | None = None

    # Заметки
    notes: list[str] | None = None

    # Рекомендации (для не сдающих)
    recommendations: list[str] | None = None

    # Флаги
    needs_attention: bool = False


# ============== PIN Verification ==============


class PinVerifyRequest(BaseModel):
    """Запрос проверки PIN-кода."""

    pin: str = Field(..., min_length=4, max_length=6, pattern=r"^\d+$")


class PinVerifyResponse(BaseModel):
    """Ответ проверки PIN-кода."""

    success: bool
    message: str | None = None
    attempts_left: int | None = None
    retry_after: int | None = Field(None, description="Секунды до следующей попытки")


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
    last_viewed_at: datetime | None
    views_by_date: dict[str, int] = Field(default_factory=dict, description="Просмотры по датам")


class ReportViewRecord(BaseModel):
    """Запись о просмотре отчёта."""

    viewed_at: datetime
    ip_address: str
    user_agent: str | None = None

    class Config:
        from_attributes = True


class ReportViewsResponse(BaseModel):
    """Ответ со статистикой просмотров."""

    report_id: UUID
    stats: ReportViewStats
    recent_views: list[ReportViewRecord] = Field(default_factory=list, description="Последние 50 просмотров")
