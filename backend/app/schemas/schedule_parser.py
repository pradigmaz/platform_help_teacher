"""
Схемы для автопарсера расписания
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ParserConfigBase(BaseModel):
    teacher_name: str = Field(..., max_length=100)
    enabled: bool = False
    days_of_week: List[int] = Field(default=[6], min_length=1, max_length=7)
    run_time: str = Field(default="20:00", pattern=r"^\d{2}:\d{2}$")
    parse_days_ahead: int = Field(default=14, ge=7, le=60)


class ParserConfigCreate(ParserConfigBase):
    pass


class ParserConfigUpdate(BaseModel):
    teacher_name: Optional[str] = None
    enabled: Optional[bool] = None
    days_of_week: Optional[List[int]] = Field(default=None, min_length=1, max_length=7)
    run_time: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    parse_days_ahead: Optional[int] = Field(default=None, ge=7, le=60)


class ParserConfigResponse(ParserConfigBase):
    id: UUID
    teacher_id: UUID
    last_run_at: Optional[datetime] = None
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


class ParseHistoryResponse(BaseModel):
    id: UUID
    teacher_id: UUID
    config_id: Optional[UUID]
    started_at: datetime
    finished_at: Optional[datetime]
    status: str
    lessons_created: int
    lessons_skipped: int
    conflicts_created: int
    error_message: Optional[str]
    
    class Config:
        from_attributes = True
