"""
Схемы для журнала (посещаемость + оценки).
"""

from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.models.attendance import AttendanceStatus

# === Attendance Journal ===


class AttendanceCell(BaseModel):
    """Ячейка посещаемости"""

    lesson_id: UUID
    status: AttendanceStatus | None = None
    attendance_id: UUID | None = None


class StudentAttendanceRow(BaseModel):
    """Строка посещаемости студента"""

    student_id: UUID
    student_name: str
    attendance: dict[str, AttendanceCell]  # lesson_id -> cell
    stats: dict[str, int]  # present, late, absent, excused, total


class LessonColumn(BaseModel):
    """Колонка занятия"""

    lesson_id: UUID
    date: date
    lesson_number: int
    lesson_type: str
    topic: str | None = None
    is_cancelled: bool = False


class AttendanceJournalResponse(BaseModel):
    """Ответ журнала посещаемости"""

    group_id: UUID
    group_name: str
    start_date: date
    end_date: date
    lessons: list[LessonColumn]
    students: list[StudentAttendanceRow]


# === Grades Journal ===


class GradeCell(BaseModel):
    """Ячейка оценки"""

    work_id: UUID
    grade: int | None = None
    submission_id: UUID | None = None
    feedback: str | None = None


class StudentGradesRow(BaseModel):
    """Строка оценок студента"""

    student_id: UUID
    student_name: str
    grades: dict[str, GradeCell]  # work_id -> cell
    average: float | None = None
    total: int = 0


class WorkColumn(BaseModel):
    """Колонка работы"""

    work_id: UUID
    title: str
    work_type: str
    max_grade: int
    deadline: date | None = None


class GradesJournalResponse(BaseModel):
    """Ответ журнала оценок"""

    group_id: UUID
    group_name: str
    work_type: str | None = None
    works: list[WorkColumn]
    students: list[StudentGradesRow]


# === Bulk Operations ===


class BulkAttendanceItem(BaseModel):
    """Элемент массового создания посещаемости"""

    student_id: UUID
    lesson_id: UUID
    status: AttendanceStatus


class BulkAttendanceCreate(BaseModel):
    """Запрос массового создания посещаемости"""

    group_id: UUID
    date: date
    lesson_number: int
    items: list[BulkAttendanceItem]


class BulkAttendanceResponse(BaseModel):
    """Ответ массового создания"""

    created: int
    updated: int
    errors: list[str] = []


class BulkGradeItem(BaseModel):
    """Элемент массового создания оценок"""

    student_id: UUID
    work_id: UUID
    grade: int
    feedback: str | None = None


class BulkGradesCreate(BaseModel):
    """Запрос массового создания оценок"""

    items: list[BulkGradeItem]


class BulkGradesResponse(BaseModel):
    """Ответ массового создания оценок"""

    created: int
    updated: int
    errors: list[str] = []
