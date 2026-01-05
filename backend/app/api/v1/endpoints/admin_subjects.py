"""
API endpoints для управления предметами.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud import crud_subject
from app.models import Subject, TeacherSubjectAssignment

logger = logging.getLogger(__name__)
router = APIRouter()


# === Schemas ===

class SubjectCreate(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None


class SubjectResponse(BaseModel):
    id: UUID
    name: str
    code: Optional[str]
    description: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class TeacherSubjectResponse(BaseModel):
    id: UUID
    subject_id: UUID
    subject_name: str
    group_id: Optional[UUID]
    group_name: Optional[str]
    semester: Optional[str]
    is_active: bool


class AssignTeacherRequest(BaseModel):
    teacher_id: UUID
    subject_id: UUID
    group_id: Optional[UUID] = None
    semester: Optional[str] = None


# === Endpoints ===

@router.get("/", response_model=List[SubjectResponse])
async def list_subjects(
    active_only: bool = Query(True),
    db: AsyncSession = Depends(deps.get_db)
):
    """Получить список всех предметов"""
    subjects = await crud_subject.get_all_subjects(db, active_only)
    return subjects


@router.post("/", response_model=SubjectResponse)
async def create_subject(
    data: SubjectCreate,
    db: AsyncSession = Depends(deps.get_db)
):
    """Создать новый предмет"""
    existing = await crud_subject.get_subject_by_name(db, data.name)
    if existing:
        raise HTTPException(status_code=400, detail="Предмет с таким названием уже существует")
    
    subject = await crud_subject.create_subject(
        db, data.name, data.code, data.description
    )
    await db.commit()
    return subject


@router.get("/{subject_id}", response_model=SubjectResponse)
async def get_subject(
    subject_id: UUID,
    db: AsyncSession = Depends(deps.get_db)
):
    """Получить предмет по ID"""
    subject = await crud_subject.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Предмет не найден")
    return subject


@router.get("/teacher/{teacher_id}", response_model=List[TeacherSubjectResponse])
async def get_teacher_subjects(
    teacher_id: UUID,
    semester: Optional[str] = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(deps.get_db)
):
    """Получить все предметы преподавателя"""
    assignments = await crud_subject.get_teacher_subjects(
        db, teacher_id, semester, active_only
    )
    
    result = []
    for a in assignments:
        result.append(TeacherSubjectResponse(
            id=a.id,
            subject_id=a.subject_id,
            subject_name=a.subject.name if a.subject else "Unknown",
            group_id=a.group_id,
            group_name=a.group.name if a.group else None,
            semester=a.semester,
            is_active=a.is_active
        ))
    return result


@router.post("/assign", response_model=dict)
async def assign_teacher_to_subject(
    data: AssignTeacherRequest,
    db: AsyncSession = Depends(deps.get_db)
):
    """Назначить преподавателя на предмет"""
    assignment = await crud_subject.assign_teacher_to_subject(
        db, data.teacher_id, data.subject_id, data.group_id, data.semester
    )
    await db.commit()
    return {"id": str(assignment.id), "message": "Преподаватель назначен на предмет"}
