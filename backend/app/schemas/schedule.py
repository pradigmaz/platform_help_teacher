"""
Схемы для расписания и занятий.
"""
from datetime import date
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.schedule import DayOfWeek, LessonType, WeekParity


# === ScheduleItem ===

class ScheduleItemBase(BaseModel):
    day_of_week: DayOfWeek
    lesson_number: int = Field(ge=1, le=8)
    lesson_type: LessonType
    subject: Optional[str] = None
    room: Optional[str] = None
    teacher_id: Optional[UUID] = None
    start_date: date
    end_date: Optional[date] = None
    week_parity: Optional[WeekParity] = None
    subgroup: Optional[int] = Field(None, ge=1, le=2)


class ScheduleItemCreate(ScheduleItemBase):
    group_id: UUID


class ScheduleItemUpdate(BaseModel):
    day_of_week: Optional[DayOfWeek] = None
    lesson_number: Optional[int] = Field(None, ge=1, le=8)
    lesson_type: Optional[LessonType] = None
    subject: Optional[str] = None
    room: Optional[str] = None
    teacher_id: Optional[UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    week_parity: Optional[WeekParity] = None
    subgroup: Optional[int] = Field(None, ge=1, le=2)
    is_active: Optional[bool] = None


class ScheduleItemResponse(ScheduleItemBase):
    id: UUID
    group_id: UUID
    is_active: bool
    
    class Config:
        from_attributes = True


# === Lesson ===

class LessonBase(BaseModel):
    date: date
    lesson_number: int = Field(ge=1, le=8)
    lesson_type: LessonType
    topic: Optional[str] = None
    work_id: Optional[UUID] = None
    subgroup: Optional[int] = Field(None, ge=1, le=2)


class LessonCreate(LessonBase):
    group_id: UUID
    schedule_item_id: Optional[UUID] = None


class LessonUpdate(BaseModel):
    topic: Optional[str] = None
    work_id: Optional[UUID] = None
    is_cancelled: Optional[bool] = None
    cancellation_reason: Optional[str] = None
    ended_early: Optional[bool] = None


class LessonResponse(LessonBase):
    id: UUID
    group_id: UUID
    schedule_item_id: Optional[UUID]
    is_cancelled: bool
    cancellation_reason: Optional[str]
    ended_early: bool = False
    
    class Config:
        from_attributes = True


# === Bulk operations ===

class GenerateLessonsRequest(BaseModel):
    """Запрос на генерацию занятий из расписания"""
    group_id: UUID
    start_date: date
    end_date: date


class GenerateLessonsResponse(BaseModel):
    """Ответ на генерацию занятий"""
    created_count: int
    lessons: List[LessonResponse]
