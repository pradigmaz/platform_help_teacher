from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from enum import Enum
from app.models.group import GradingScale


# Базовая схема студента при импорте
class StudentImport(BaseModel):
    full_name: str
    username: Optional[str] = None
    email: Optional[str] = None

# Студент в ответе группы
class StudentInGroupResponse(BaseModel):
    id: UUID
    full_name: str
    username: Optional[str] = None
    invite_code: Optional[str] = None
    subgroup: Optional[int] = None
    is_active: bool = True

    class Config:
        from_attributes = True


# Обновление студента
class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    subgroup: Optional[int] = None  # 1, 2, или None (убрать подгруппу)


# Массовое назначение подгруппы
class AssignSubgroupRequest(BaseModel):
    subgroup: Optional[int] = None  # 1, 2, или None
    names: List[str]  # Список ФИО для поиска


class AssignSubgroupResponse(BaseModel):
    matched: int
    updated_students: List[str]
    not_found: List[str]

# То, что присылает фронтенд при создании
class GroupCreate(BaseModel):
    name: str
    code: str
    students: List[StudentImport] = []
    # Настройки лабораторных (опционально)
    labs_count: Optional[int] = None
    grading_scale: Optional[GradingScale] = GradingScale.TEN
    default_max_grade: Optional[int] = 10
    has_subgroups: bool = True


# Схема для обновления настроек лабораторных
class LabSettingsUpdate(BaseModel):
    labs_count: Optional[int] = None
    grading_scale: Optional[GradingScale] = None
    default_max_grade: Optional[int] = None
    has_subgroups: Optional[bool] = None


# То, что отдаем обратно (в списки)
class GroupResponse(BaseModel):
    id: UUID
    name: str
    code: str
    invite_code: Optional[str] = None
    created_at: datetime
    students_count: Optional[int] = 0
    # Настройки лабораторных
    labs_count: Optional[int] = None
    grading_scale: Optional[GradingScale] = None
    default_max_grade: Optional[int] = None
    has_subgroups: bool = True

    class Config:
        from_attributes = True


# Детальный ответ группы со студентами
class GroupDetailResponse(BaseModel):
    id: UUID
    name: str
    code: str
    invite_code: Optional[str] = None
    created_at: datetime
    students: List[StudentInGroupResponse] = []
    # Настройки лабораторных
    labs_count: Optional[int] = None
    grading_scale: Optional[GradingScale] = None
    default_max_grade: Optional[int] = None
    has_subgroups: bool = True

    class Config:
        from_attributes = True