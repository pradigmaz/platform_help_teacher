"""Student management within groups."""
from typing import Any, List
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app import schemas, models
from app.api import deps
from app.db.session import get_db
from app.core.limiter import limiter
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class BulkStudentsRequest(BaseModel):
    names: List[str] = Field(..., min_length=1, max_length=200)


class BulkStudentsResponse(BaseModel):
    added: int
    students: List[schemas.StudentInGroupResponse]


class BulkDeleteRequest(BaseModel):
    student_ids: List[UUID] = Field(..., min_length=1, max_length=200)


class BulkDeleteResponse(BaseModel):
    deleted: int


@router.post("/{group_id}/students", response_model=schemas.StudentInGroupResponse)
@limiter.limit("30/minute")
async def add_student(
    request: Request,
    group_id: UUID,
    student_data: schemas.StudentImport,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Добавить студента в группу вручную."""
    result = await db.execute(select(models.Group).where(models.Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    student = models.User(
        full_name=student_data.full_name,
        username=student_data.username,
        group_id=group_id,
        role=models.user.UserRole.STUDENT,
    )
    db.add(student)
    
    try:
        await db.commit()
        await db.refresh(student)
        return student
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Error adding student: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@router.post("/{group_id}/students/bulk", response_model=BulkStudentsResponse)
@limiter.limit("10/minute")
async def add_students_bulk(
    request: Request,
    group_id: UUID,
    data: BulkStudentsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Массовое добавление студентов в группу (для импорта)."""
    if len(data.names) > settings.MAX_STUDENTS_COUNT:
        raise HTTPException(
            status_code=400,
            detail=f"Слишком много студентов (максимум {settings.MAX_STUDENTS_COUNT})"
        )
    
    result = await db.execute(select(models.Group).where(models.Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    added_students = []
    for name in data.names:
        name = name.strip()
        if not name:
            continue
        student = models.User(
            full_name=name,
            group_id=group_id,
            role=models.user.UserRole.STUDENT,
        )
        db.add(student)
        added_students.append(student)
    
    try:
        await db.commit()
        for s in added_students:
            await db.refresh(s)
        return BulkStudentsResponse(
            added=len(added_students),
            students=added_students
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Error bulk adding students: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@router.delete("/{group_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def remove_student(
    request: Request,
    group_id: UUID,
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> None:
    """Удалить студента."""
    result = await db.execute(
        select(models.User).where(
            models.User.id == student_id,
            models.User.group_id == group_id
        )
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    try:
        await db.delete(student)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error")


@router.patch("/{group_id}/students/{student_id}", response_model=schemas.StudentInGroupResponse)
async def update_student(
    group_id: UUID,
    student_id: UUID,
    student_in: schemas.StudentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Обновить студента (ФИО, подгруппа)."""
    result = await db.execute(
        select(models.User).where(
            models.User.id == student_id,
            models.User.group_id == group_id
        )
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    try:
        if student_in.full_name is not None:
            student.full_name = student_in.full_name
        if student_in.subgroup is not None or 'subgroup' in student_in.model_fields_set:
            student.subgroup = student_in.subgroup
        await db.commit()
        await db.refresh(student)
        return student
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Error updating student: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@router.post("/{group_id}/students/bulk-delete", response_model=BulkDeleteResponse)
@limiter.limit("10/minute")
async def delete_students_bulk(
    request: Request,
    group_id: UUID,
    data: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Массовое удаление студентов из группы."""
    result = await db.execute(
        select(models.User).where(
            models.User.id.in_(data.student_ids),
            models.User.group_id == group_id
        )
    )
    students = list(result.scalars().all())
    
    if not students:
        raise HTTPException(status_code=404, detail="Students not found")
    
    try:
        for student in students:
            await db.delete(student)
        await db.commit()
        return BulkDeleteResponse(deleted=len(students))
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Error bulk deleting students: {e}")
        raise HTTPException(status_code=500, detail="Database error")
