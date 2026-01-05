"""
Pydantic схемы для API посещаемости.

Requirements:
- 8.1: store attendance records with student, group, date, and status
- 8.2: support attendance status types: PRESENT, ABSENT, LATE, EXCUSED
"""
from typing import Optional, List
from uuid import UUID
from datetime import date as date_type, datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from app.models.attendance import AttendanceStatus as AttendanceStatusSchema


class AttendanceCreate(BaseModel):
    """Схема создания записи посещаемости"""
    student_id: UUID = Field(description="ID студента")
    group_id: UUID = Field(description="ID группы")
    date: date_type = Field(description="Дата занятия")
    status: AttendanceStatusSchema = Field(
        default=AttendanceStatusSchema.ABSENT,
        description="Статус посещаемости"
    )

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: date_type) -> date_type:
        if v > date_type.today():
             raise ValueError("Date cannot be in the future")
        return v


class AttendanceUpdate(BaseModel):
    """Схема обновления записи посещаемости"""
    status: AttendanceStatusSchema = Field(description="Новый статус посещаемости")


class AttendanceResponse(BaseModel):
    """Схема ответа с записью посещаемости"""
    id: UUID
    student_id: UUID
    group_id: UUID
    date: date_type
    status: AttendanceStatusSchema
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BulkAttendanceItem(BaseModel):
    """Элемент массового создания посещаемости"""
    student_id: UUID = Field(description="ID студента")
    status: AttendanceStatusSchema = Field(description="Статус посещаемости")


class BulkAttendanceCreate(BaseModel):
    """Схема массового создания записей посещаемости"""
    group_id: UUID = Field(description="ID группы")
    date: date_type = Field(description="Дата занятия")
    records: List[BulkAttendanceItem] = Field(description="Список записей")

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: date_type) -> date_type:
        if v > date_type.today():
             raise ValueError("Date cannot be in the future")
        return v


class BulkAttendanceResponse(BaseModel):
    """Ответ на массовое создание посещаемости"""
    created_count: int = Field(description="Количество созданных записей")
    skipped_count: int = Field(description="Количество пропущенных записей")
    records: List[AttendanceResponse] = Field(description="Созданные записи")


class AttendanceStatsResponse(BaseModel):
    """Статистика посещаемости студента"""
    student_id: UUID
    total_classes: int = Field(description="Всего занятий")
    present_count: int = Field(description="Присутствовал")
    late_count: int = Field(description="Опоздал")
    excused_count: int = Field(description="Уважительная причина")
    absent_count: int = Field(description="Отсутствовал")
    attendance_rate: float = Field(description="Процент посещаемости")
