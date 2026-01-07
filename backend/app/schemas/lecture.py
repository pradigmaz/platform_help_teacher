from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
import json
from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.constants import LECTURE_MAX_IMAGES_RESPONSE

# Константы валидации контента
MAX_CONTENT_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
MAX_CONTENT_DEPTH = 50


def _check_depth(obj: Any, current_depth: int = 0) -> int:
    """Проверяет глубину вложенности JSON."""
    if current_depth > MAX_CONTENT_DEPTH:
        return current_depth
    if isinstance(obj, dict):
        if not obj:
            return current_depth
        return max(_check_depth(v, current_depth + 1) for v in obj.values())
    if isinstance(obj, list):
        if not obj:
            return current_depth
        return max(_check_depth(v, current_depth + 1) for v in obj)
    return current_depth


class LectureImageResponse(BaseModel):
    id: UUID
    lecture_id: UUID
    filename: str
    storage_path: str
    mime_type: str
    size_bytes: int
    created_at: datetime

    class Config:
        from_attributes = True


class SubjectBrief(BaseModel):
    id: UUID
    name: str
    code: Optional[str] = None

    class Config:
        from_attributes = True


class LectureCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    content: Dict[str, Any] = Field(default_factory=dict)
    subject_id: Optional[UUID] = None

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        # Проверка размера
        content_str = json.dumps(v, ensure_ascii=False)
        if len(content_str.encode('utf-8')) > MAX_CONTENT_SIZE_BYTES:
            raise ValueError(f'Content exceeds {MAX_CONTENT_SIZE_BYTES // (1024*1024)}MB limit')
        # Проверка глубины вложенности
        depth = _check_depth(v)
        if depth > MAX_CONTENT_DEPTH:
            raise ValueError(f'Content nesting depth exceeds {MAX_CONTENT_DEPTH} levels')
        return v


class LectureUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    content: Optional[Dict[str, Any]] = None
    subject_id: Optional[UUID] = None

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if v is None:
            return v
        content_str = json.dumps(v, ensure_ascii=False)
        if len(content_str.encode('utf-8')) > MAX_CONTENT_SIZE_BYTES:
            raise ValueError(f'Content exceeds {MAX_CONTENT_SIZE_BYTES // (1024*1024)}MB limit')
        depth = _check_depth(v)
        if depth > MAX_CONTENT_DEPTH:
            raise ValueError(f'Content nesting depth exceeds {MAX_CONTENT_DEPTH} levels')
        return v


class LectureResponse(BaseModel):
    id: UUID
    title: str
    content: Dict[str, Any]
    is_published: bool
    public_code: Optional[str] = None
    subject_id: Optional[UUID] = None
    subject: Optional[SubjectBrief] = None
    created_at: datetime
    updated_at: datetime
    images: List[LectureImageResponse] = Field(default_factory=list)
    images_total: Optional[int] = None

    class Config:
        from_attributes = True

    @model_validator(mode='after')
    def limit_images(self):
        if self.images:
            self.images_total = len(self.images)
            self.images = self.images[:LECTURE_MAX_IMAGES_RESPONSE]
        return self


class LectureListResponse(BaseModel):
    id: UUID
    title: str
    is_published: bool
    public_code: Optional[str] = None
    subject_id: Optional[UUID] = None
    subject: Optional[SubjectBrief] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PublicLinkResponse(BaseModel):
    public_code: str
    url: str
