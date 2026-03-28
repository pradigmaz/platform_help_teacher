import json
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.constants import (
    LAB_CONTENT_MAX_SIZE_BYTES,
    LAB_MAX_QUESTIONS,
    LAB_MAX_VARIANTS,
)
from app.models.submission import SubmissionStatus

# === Validators ===


def validate_jsonb_size(v: dict[str, Any] | None, max_bytes: int = LAB_CONTENT_MAX_SIZE_BYTES) -> dict[str, Any] | None:
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
    grade: int | None = None
    feedback: str | None = None
    s3_key: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# === Lab Create/Update Schemas ===


class LabCreate(BaseModel):
    """Схема создания лабораторной работы."""

    number: int = Field(default=1, ge=1, description="Порядковый номер лабы")
    title: str = Field(..., min_length=1, max_length=200)
    topic: str | None = None
    goal: str | None = None
    formatting_guide: str | None = None
    description: str | None = None
    theory_content: dict[str, Any] | None = None
    practice_content: dict[str, Any] | None = None
    variants: list[dict[str, Any]] | None = None
    questions: list[Any] | None = None  # str (legacy) или Dict (Lexical JSON)
    max_grade: int = Field(default=5, ge=1, le=100)
    deadline_5_lessons: int | None = Field(default=None, ge=1, description="Через сколько пар блокируется 5")
    deadline_4_lessons: int | None = Field(default=None, ge=1, description="Через сколько пар блокируется 4")
    is_sequential: bool = True
    subject_id: UUID | None = None
    lesson_id: UUID | None = None

    @field_validator("theory_content", "practice_content")
    @classmethod
    def validate_content_size(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        return validate_jsonb_size(v)

    @field_validator("variants")
    @classmethod
    def validate_variants(cls, v: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
        if v is not None:
            if len(v) > LAB_MAX_VARIANTS:
                raise ValueError(f"Too many variants: {len(v)} (max {LAB_MAX_VARIANTS})")
            # Валидация общего размера
            size = len(json.dumps(v, ensure_ascii=False))
            if size > LAB_CONTENT_MAX_SIZE_BYTES:
                raise ValueError(f"Variants too large: {size} bytes")
        return v

    @field_validator("questions")
    @classmethod
    def validate_questions(cls, v: list[Any] | None) -> list[Any] | None:
        if v is not None and len(v) > LAB_MAX_QUESTIONS:
            raise ValueError(f"Too many questions: {len(v)} (max {LAB_MAX_QUESTIONS})")
        return v


class LabUpdate(BaseModel):
    """Схема обновления лабораторной работы."""

    number: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    topic: str | None = None
    goal: str | None = None
    formatting_guide: str | None = None
    description: str | None = None
    theory_content: dict[str, Any] | None = None
    practice_content: dict[str, Any] | None = None
    variants: list[dict[str, Any]] | None = None
    questions: list[Any] | None = None  # str (legacy) или Dict (Lexical JSON)
    max_grade: int | None = Field(default=None, ge=1, le=100)
    deadline_5_lessons: int | None = Field(default=None, ge=1)
    deadline_4_lessons: int | None = Field(default=None, ge=1)
    is_sequential: bool | None = None
    subject_id: UUID | None = None
    lesson_id: UUID | None = None

    @field_validator("theory_content", "practice_content")
    @classmethod
    def validate_content_size(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        return validate_jsonb_size(v)

    @field_validator("variants")
    @classmethod
    def validate_variants(cls, v: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
        if v is not None:
            if len(v) > LAB_MAX_VARIANTS:
                raise ValueError(f"Too many variants: {len(v)} (max {LAB_MAX_VARIANTS})")
            size = len(json.dumps(v, ensure_ascii=False))
            if size > LAB_CONTENT_MAX_SIZE_BYTES:
                raise ValueError(f"Variants too large: {size} bytes")
        return v

    @field_validator("questions")
    @classmethod
    def validate_questions(cls, v: list[Any] | None) -> list[Any] | None:
        if v is not None and len(v) > LAB_MAX_QUESTIONS:
            raise ValueError(f"Too many questions: {len(v)} (max {LAB_MAX_QUESTIONS})")
        return v


# === Lab Response Schemas ===


class LabOut(BaseModel):
    """Краткая схема лабы для списков."""

    id: UUID
    number: int
    title: str
    description: str | None = None
    max_grade: int
    deadline_5_lessons: int | None = None
    deadline_4_lessons: int | None = None
    is_published: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LabResponse(BaseModel):
    """Схема лабы для списка с submission."""

    id: UUID
    title: str
    description: str | None = None
    deadline_5_lessons: int | None = None
    deadline_4_lessons: int | None = None
    max_grade: int
    s3_key: str | None = None
    my_submission: SubmissionDTO | None = None

    class Config:
        from_attributes = True


class LabDetailResponse(BaseModel):
    """Полная схема лабы для детального просмотра."""

    id: UUID
    number: int
    title: str
    topic: str | None = None
    goal: str | None = None
    formatting_guide: str | None = None
    description: str | None = None
    theory_content: dict[str, Any] | None = None
    practice_content: dict[str, Any] | None = None
    variants: list[dict[str, Any]] | None = None
    questions: list[Any] | None = None  # str (legacy) или Dict (Lexical JSON)
    deadline_5_lessons: int | None = None
    deadline_4_lessons: int | None = None
    max_grade: int
    is_sequential: bool
    is_published: bool
    public_code: str | None = None
    subject_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PublishLabResponse(BaseModel):
    """Ответ на публикацию лабы."""

    status: str
    public_code: str | None = None
