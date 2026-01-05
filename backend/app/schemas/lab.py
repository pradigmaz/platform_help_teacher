from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from enum import Enum
from app.models.submission import SubmissionStatus

# Базовая схема Submission для встраивания в Lab
class SubmissionDTO(BaseModel):
    id: UUID
    status: SubmissionStatus
    grade: Optional[int] = None
    feedback: Optional[str] = None
    s3_key: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Схема Лабы для списка
class LabResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    max_grade: int
    s3_key: Optional[str] = None # Файл задания
    
    # Вложенное поле: сдача текущего юзера (если есть)
    my_submission: Optional[SubmissionDTO] = None

    class Config:
        from_attributes = True