"""
Схемы для автопарсера расписания
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ParserConfigBase(BaseModel):
    teacher_name: str = Field(..., max_length=100)
    enabled: bool = False
    days_of_week: list[int] = Field(default=[6], min_length=1, max_length=7)
    run_time: str = Field(default="20:00", pattern=r"^\d{2}:\d{2}$")
    parse_days_ahead: int = Field(default=14, ge=7, le=60)


class ParserConfigCreate(ParserConfigBase):
    pass


class ParserConfigUpdate(BaseModel):
    teacher_name: str | None = None
    enabled: bool | None = None
    days_of_week: list[int] | None = Field(default=None, min_length=1, max_length=7)
    run_time: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    parse_days_ahead: int | None = Field(default=None, ge=7, le=60)


class ParserConfigResponse(ParserConfigBase):
    id: UUID
    teacher_id: UUID
    last_run_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConflictOldData(BaseModel):
    topic: str | None = None
    lesson_type: str | None = None
    room: str | None = None
    date: str | None = None
    lesson_number: int | None = None


class ConflictNewData(BaseModel):
    topic: str | None = None
    lesson_type: str | None = None
    room: str | None = None
    date: str | None = None
    lesson_number: int | None = None


class ScheduleConflictResponse(BaseModel):
    id: UUID
    lesson_id: UUID
    conflict_type: str
    old_data: dict
    new_data: dict | None
    resolved: bool
    resolution: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ConflictResolveRequest(BaseModel):
    action: str = Field(..., pattern=r"^(accept|reject)$")


class ParseHistoryResponse(BaseModel):
    id: UUID
    teacher_id: UUID
    config_id: UUID | None
    started_at: datetime
    finished_at: datetime | None
    status: str
    lessons_created: int
    lessons_skipped: int
    conflicts_created: int
    error_message: str | None

    class Config:
        from_attributes = True
