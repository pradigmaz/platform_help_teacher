"""
Схемы для журнала (посещаемость + оценки).
"""
from datetime import date
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.attendance import AttendanceStatus


# === Attendance Journal ===

class AttendanceCell(BaseModel):
    """Ячейка посещаемости"""
    lesson_id: UUID
    status: Optional[AttendanceStatus] = None
    attendance_id: Optional[UUID] = None


class StudentAttendanceRow(BaseModel):
    """Строка посещаемости студента"""
    student_id: UUID
    student_name: str
    attendance: Dict[str, AttendanceCell]  # lesson_id -> cell
    stats: Dict[str, int]  # present, late, absent, excused, total


class LessonColumn(BaseModel):
    """Колонка занятия"""
    lesson_id: UUID
    date: date
    lesson_number: int
    lesson_type: str
    topic: Optional[str] = None
    is_cancelled: bool = False


class AttendanceJournalResponse(BaseModel):
    """Ответ журнала посещаемости"""
    group_id: UUID
    group_name: str
    start_date: date
    end_date: date
    lessons: List[LessonColumn]
    students: List[StudentAttendanceRow]


# === Grades Journal ===

class GradeCell(BaseModel):
    """Ячейка оценки"""
    work_id: UUID
    grade: Optional[int] = None
    submission_id: Optional[UUID] = None
    feedback: Optional[str] = None


class StudentGradesRow(BaseModel):
    """Строка оценок студента"""
    student_id: UUID
    student_name: str
    grades: Dict[str, GradeCell]  # work_id -> cell
    average: Optional[float] = None
    total: int = 0


class WorkColumn(BaseModel):
    """Колонка работы"""
    work_id: UUID
    title: str
    work_type: str
    max_grade: int
    deadline: Optional[date] = None


class GradesJournalResponse(BaseModel):
    """Ответ журнала оценок"""
    group_id: UUID
    group_name: str
    work_type: Optional[str] = None
    works: List[WorkColumn]
    students: List[StudentGradesRow]


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
    items: List[BulkAttendanceItem]


class BulkAttendanceResponse(BaseModel):
    """Ответ массового создания"""
    created: int
    updated: int
    errors: List[str] = []


class BulkGradeItem(BaseModel):
    """Элемент массового создания оценок"""
    student_id: UUID
    work_id: UUID
    grade: int
    feedback: Optional[str] = None


class BulkGradesCreate(BaseModel):
    """Запрос массового создания оценок"""
    items: List[BulkGradeItem]


class BulkGradesResponse(BaseModel):
    """Ответ массового создания оценок"""
    created: int
    updated: int
    errors: List[str] = []
