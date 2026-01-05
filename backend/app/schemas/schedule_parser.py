"""
Схемы для автопарсера расписания
"""
from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ParserConfigBase(BaseModel):
    teacher_name: str = Field(..., max_length=100)
    enabled: bool = False
    day_of_week: int = Field(default=6, ge=0, le=6)  # 0=пн, 6=вс
    run_time: str = Field(default="20:00", pattern=r"^\d{2}:\d{2}$")
    parse_days_ahead: int = Field(default=14, ge=7, le=60)


class ParserConfigCreate(ParserConfigBase):
    pass


class ParserConfigUpdate(BaseModel):
    teacher_name: Optional[str] = None
    enabled: Optional[bool] = None
    day_of_week: Optional[int] = Field(default=None, ge=0, le=6)
    run_time: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    parse_days_ahead: Optional[int] = Field(default=None, ge=7, le=60)


class ParserConfigResponse(ParserConfigBase):
    id: UUID
    teacher_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConflictOldData(BaseModel):
    topic: Optional[str] = None
    lesson_type: Optional[str] = None
    room: Optional[str] = None
    date: Optional[str] = None
    lesson_number: Optional[int] = None


class ConflictNewData(BaseModel):
    topic: Optional[str] = None
    lesson_type: Optional[str] = None
    room: Optional[str] = None
    date: Optional[str] = None
    lesson_number: Optional[int] = None


class ScheduleConflictResponse(BaseModel):
    id: UUID
    lesson_id: UUID
    conflict_type: str
    old_data: dict
    new_data: Optional[dict]
    resolved: bool
    resolution: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConflictResolveRequest(BaseModel):
    action: str = Field(..., pattern=r"^(accept|reject)$")
