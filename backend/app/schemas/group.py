from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.group import GradingScale


# Базовая схема студента при импорте
class StudentImport(BaseModel):
    full_name: str
    username: str | None = None
    email: str | None = None

# Студент в ответе группы
class StudentInGroupResponse(BaseModel):
    id: UUID
    full_name: str
    username: str | None = None
    vk_id: int | None = None
    invite_code: str | None = None
    subgroup: Literal[1, 2] | None = None
    is_active: bool = True

    class Config:
        from_attributes = True


# Обновление студента
class StudentUpdate(BaseModel):
    full_name: str | None = None
    subgroup: Literal[1, 2] | None = None


# Массовое назначение подгруппы
class AssignSubgroupRequest(BaseModel):
    subgroup: Literal[1, 2] | None = None
    names: list[str]


class AssignSubgroupResponse(BaseModel):
    matched: int
    updated_students: list[str]
    not_found: list[str]


class ClearSubgroupsResponse(BaseModel):
    cleared: int

# То, что присылает фронтенд при создании
class GroupCreate(BaseModel):
    name: str
    code: str
    students: list[StudentImport] = []
    labs_count: int | None = Field(default=None, ge=0, le=50)
    grading_scale: GradingScale | None = GradingScale.TEN
    default_max_grade: int | None = Field(default=10, ge=1, le=100)
    has_subgroups: bool = True


# Схема для обновления настроек лабораторных
class LabSettingsUpdate(BaseModel):
    labs_count: int | None = Field(default=None, ge=0, le=50)
    grading_scale: GradingScale | None = None
    default_max_grade: int | None = Field(default=None, ge=1, le=100)
    has_subgroups: bool | None = None


# То, что отдаем обратно (в списки)
class GroupResponse(BaseModel):
    id: UUID
    name: str
    code: str
    invite_code: str | None = None
    created_at: datetime
    students_count: int | None = 0
    is_archived: bool = False
    # Настройки лабораторных
    labs_count: int | None = None
    grading_scale: GradingScale | None = None
    default_max_grade: int | None = None
    has_subgroups: bool = True

    class Config:
        from_attributes = True


# Детальный ответ группы со студентами
class GroupDetailResponse(BaseModel):
    id: UUID
    name: str
    code: str
    invite_code: str | None = None
    created_at: datetime
    students: list[StudentInGroupResponse] = []
    # Настройки лабораторных
    labs_count: int | None = None
    grading_scale: GradingScale | None = None
    default_max_grade: int | None = None
    has_subgroups: bool = True

    class Config:
        from_attributes = True
