from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field


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


class LectureUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    content: Optional[Dict[str, Any]] = None
    subject_id: Optional[UUID] = None


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

    class Config:
        from_attributes = True


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
