import json
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.submission import SubmissionStatus
from app.core.constants import (
    LAB_CONTENT_MAX_SIZE_BYTES,
    LAB_MAX_VARIANTS,
    LAB_MAX_QUESTIONS,
)


# === Validators ===

def validate_jsonb_size(v: Optional[Dict[str, Any]], max_bytes: int = LAB_CONTENT_MAX_SIZE_BYTES) -> Optional[Dict[str, Any]]:
    """Валидация размера JSONB контента."""
    if v is not None:
        size = len(json.dumps(v, ensure_ascii=False))
        if size > max_bytes:
            raise ValueError(f"Content too large: {size} bytes (max {max_bytes})")
    return v


# === Submission Schemas ===

class SubmissionDTO(BaseModel):
    """Базовая схема Submission для встраивания в Lab."""
    id: UUID
    status: SubmissionStatus
    grade: Optional[int] = None
    feedback: Optional[str] = None
    s3_key: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# === Lab Create/Update Schemas ===

class LabCreate(BaseModel):
    """Схема создания лабораторной работы."""
    number: int = Field(default=1, ge=1, description="Порядковый номер лабы")
    title: str = Field(..., min_length=1, max_length=200)
    topic: Optional[str] = None
    goal: Optional[str] = None
    formatting_guide: Optional[str] = None
    description: Optional[str] = None
    theory_content: Optional[Dict[str, Any]] = None
    practice_content: Optional[Dict[str, Any]] = None
    variants: Optional[List[Dict[str, Any]]] = None
    questions: Optional[List[str]] = None
    max_grade: int = Field(default=5, ge=1, le=100)
    deadline: Optional[datetime] = None
    is_sequential: bool = True
    subject_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None

    @field_validator('theory_content', 'practice_content')
    @classmethod
    def validate_content_size(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        return validate_jsonb_size(v)

    @field_validator('variants')
    @classmethod
    def validate_variants(cls, v: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        if v is not None:
            if len(v) > LAB_MAX_VARIANTS:
                raise ValueError(f"Too many variants: {len(v)} (max {LAB_MAX_VARIANTS})")
            # Валидация общего размера
            size = len(json.dumps(v, ensure_ascii=False))
            if size > LAB_CONTENT_MAX_SIZE_BYTES:
                raise ValueError(f"Variants too large: {size} bytes")
        return v

    @field_validator('questions')
    @classmethod
    def validate_questions(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            if len(v) > LAB_MAX_QUESTIONS:
                raise ValueError(f"Too many questions: {len(v)} (max {LAB_MAX_QUESTIONS})")
        return v


class LabUpdate(BaseModel):
    """Схема обновления лабораторной работы."""
    number: Optional[int] = Field(default=None, ge=1)
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    topic: Optional[str] = None
    goal: Optional[str] = None
    formatting_guide: Optional[str] = None
    description: Optional[str] = None
    theory_content: Optional[Dict[str, Any]] = None
    practice_content: Optional[Dict[str, Any]] = None
    variants: Optional[List[Dict[str, Any]]] = None
    questions: Optional[List[str]] = None
    max_grade: Optional[int] = Field(default=None, ge=1, le=100)
    deadline: Optional[datetime] = None
    is_sequential: Optional[bool] = None
    subject_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None

    @field_validator('theory_content', 'practice_content')
    @classmethod
    def validate_content_size(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        return validate_jsonb_size(v)

    @field_validator('variants')
    @classmethod
    def validate_variants(cls, v: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        if v is not None:
            if len(v) > LAB_MAX_VARIANTS:
                raise ValueError(f"Too many variants: {len(v)} (max {LAB_MAX_VARIANTS})")
            size = len(json.dumps(v, ensure_ascii=False))
            if size > LAB_CONTENT_MAX_SIZE_BYTES:
                raise ValueError(f"Variants too large: {size} bytes")
        return v

    @field_validator('questions')
    @classmethod
    def validate_questions(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            if len(v) > LAB_MAX_QUESTIONS:
                raise ValueError(f"Too many questions: {len(v)} (max {LAB_MAX_QUESTIONS})")
        return v


# === Lab Response Schemas ===

class LabOut(BaseModel):
    """Краткая схема лабы для списков."""
    id: UUID
    number: int
    title: str
    description: Optional[str] = None
    max_grade: int
    deadline: Optional[datetime] = None
    is_published: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LabResponse(BaseModel):
    """Схема лабы для списка с submission."""
    id: UUID
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    max_grade: int
    s3_key: Optional[str] = None
    my_submission: Optional[SubmissionDTO] = None

    class Config:
        from_attributes = True


class LabDetailResponse(BaseModel):
    """Полная схема лабы для детального просмотра."""
    id: UUID
    number: int
    title: str
    topic: Optional[str] = None
    goal: Optional[str] = None
    formatting_guide: Optional[str] = None
    description: Optional[str] = None
    theory_content: Optional[Dict[str, Any]] = None
    practice_content: Optional[Dict[str, Any]] = None
    variants: Optional[List[Dict[str, Any]]] = None
    questions: Optional[List[str]] = None
    deadline: Optional[datetime] = None
    max_grade: int
    is_sequential: bool
    is_published: bool
    public_code: Optional[str] = None
    subject_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PublishLabResponse(BaseModel):
    """Ответ на публикацию лабы."""
    status: str
    public_code: Optional[str] = None