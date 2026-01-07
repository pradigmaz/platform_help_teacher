"""Student management within groups."""
from typing import Any
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app import schemas, models
from app.api import deps
from app.db.session import get_db
from app.core.limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter()


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
