"""Схемы для заметок."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    LESSON = "lesson"
    STUDENT = "student"
    GROUP = "group"
    WORK = "work"
    SCHEDULE_ITEM = "schedule_item"


class NoteColor(str, Enum):
    DEFAULT = "default"
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"
    PURPLE = "purple"


class NoteCreate(BaseModel):
    entity_type: EntityType
    entity_id: UUID
    content: str = Field(..., min_length=1, max_length=2000)
    color: NoteColor = NoteColor.DEFAULT
    is_pinned: bool = False


class NoteUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=2000)
    color: Optional[NoteColor] = None
    is_pinned: Optional[bool] = None


class NoteResponse(BaseModel):
    id: UUID
    entity_type: str
    entity_id: UUID
    content: str
    color: str
    is_pinned: bool
    author_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotesListResponse(BaseModel):
    notes: List[NoteResponse]
    count: int
