"""
Схемы для расписания и занятий.
"""
from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.schedule import DayOfWeek, LessonType, WeekParity

# === ScheduleItem ===

class ScheduleItemBase(BaseModel):
    day_of_week: DayOfWeek
    lesson_number: int = Field(ge=1, le=8)
    lesson_type: LessonType
    subject: str | None = None
    room: str | None = None
    teacher_id: UUID | None = None
    start_date: date
    end_date: date | None = None
    week_parity: WeekParity | None = None
    subgroup: int | None = Field(None, ge=1, le=2)


class ScheduleItemCreate(ScheduleItemBase):
    group_id: UUID


class ScheduleItemUpdate(BaseModel):
    day_of_week: DayOfWeek | None = None
    lesson_number: int | None = Field(None, ge=1, le=8)
    lesson_type: LessonType | None = None
    subject: str | None = None
    room: str | None = None
    teacher_id: UUID | None = None
    start_date: date | None = None
    end_date: date | None = None
    week_parity: WeekParity | None = None
    subgroup: int | None = Field(None, ge=1, le=2)
    is_active: bool | None = None


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
    topic: str | None = None
    work_id: UUID | None = None
    subgroup: int | None = Field(None, ge=1, le=2)


class LessonCreate(LessonBase):
    group_id: UUID
    schedule_item_id: UUID | None = None


class LessonUpdate(BaseModel):
    topic: str | None = None
    work_id: UUID | None = None
    work_number: int | None = Field(None, ge=1, le=20, description="Номер лабы/практики")
    is_cancelled: bool | None = None
    cancellation_reason: str | None = None
    ended_early: bool | None = None


class LessonResponse(LessonBase):
    id: UUID
    group_id: UUID
    schedule_item_id: UUID | None
    is_cancelled: bool
    cancellation_reason: str | None
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
    lessons: list[LessonResponse]
