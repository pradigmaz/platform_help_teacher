"""
Pydantic схемы для оценок за занятия.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LessonGradeBase(BaseModel):
    work_number: Optional[int] = Field(None, description="Номер работы (может отличаться от lesson.work_number)")
    grade: int = Field(..., ge=2, le=5, description="Оценка 2-5")
    comment: Optional[str] = Field(None, max_length=500)


class LessonGradeCreate(LessonGradeBase):
    lesson_id: UUID
    student_id: UUID


class LessonGradeUpdate(BaseModel):
    grade: Optional[int] = Field(None, ge=2, le=5)
    work_number: Optional[int] = None
    comment: Optional[str] = Field(None, max_length=500)


class LessonGradeResponse(LessonGradeBase):
    id: UUID
    lesson_id: UUID
    student_id: UUID
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LessonGradeWithStudent(LessonGradeResponse):
    student_name: Optional[str] = None


class GradeItem(BaseModel):
    """Элемент для массового создания оценок."""
    student_id: UUID
    grade: int = Field(..., ge=2, le=5)
    work_number: Optional[int] = Field(None, ge=1, le=20)
    comment: Optional[str] = Field(None, max_length=500)


class BulkGradeCreate(BaseModel):
    """Массовое создание/обновление оценок."""
    lesson_id: UUID
    grades: list[GradeItem]


class AttendanceRecord(BaseModel):
    """Запись посещаемости для bulk операций."""
    student_id: UUID
    status: str  # AttendanceStatus value


class BulkAttendanceUpdate(BaseModel):
    """Массовое обновление посещаемости."""
    lesson_id: UUID
    records: list[AttendanceRecord]
