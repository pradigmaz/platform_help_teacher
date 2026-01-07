"""Схемы для перевода студентов"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from uuid import UUID
from enum import Enum


class AttestationType(str, Enum):
    FIRST = "first"
    SECOND = "second"


# Данные посещаемости в снапшоте
class AttendanceSnapshot(BaseModel):
    total_lessons: int = 0
    present: int = 0
    late: int = 0
    excused: int = 0
    absent: int = 0


# Оценка за лабу в снапшоте
class LabGradeSnapshot(BaseModel):
    work_number: int
    grade: int
    lesson_id: Optional[str] = None


# Запрос на перевод
class TransferRequest(BaseModel):
    to_group_id: UUID
    to_subgroup: Optional[int] = None
    transfer_date: Optional[date] = None  # default: today
    attestation_type: AttestationType = AttestationType.FIRST


# Ответ с информацией о переводе
class TransferResponse(BaseModel):
    id: UUID
    student_id: UUID
    student_name: str
    from_group_id: Optional[UUID] = None
    from_group_name: Optional[str] = None
    from_subgroup: Optional[int] = None
    to_group_id: Optional[UUID] = None
    to_group_name: Optional[str] = None
    to_subgroup: Optional[int] = None
    transfer_date: date
    attestation_type: AttestationType
    attendance_data: AttendanceSnapshot
    lab_grades_data: List[LabGradeSnapshot]
    activity_points: float
    created_at: str

    class Config:
        from_attributes = True


# Краткая информация о переводе для списка
class TransferSummary(BaseModel):
    id: UUID
    from_group_name: Optional[str] = None
    from_subgroup: Optional[int] = None
    to_group_name: Optional[str] = None
    to_subgroup: Optional[int] = None
    transfer_date: date
    attestation_type: AttestationType

    class Config:
        from_attributes = True


# Список переводов студента
class StudentTransfersResponse(BaseModel):
    student_id: UUID
    student_name: str
    transfers: List[TransferSummary]
