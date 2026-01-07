"""Subgroup assignment operations."""
from typing import Any
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app import schemas, models
from app.api import deps
from app.db.session import get_db
from app.utils.text import fio_matches

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/{group_id}/assign-subgroup", response_model=schemas.AssignSubgroupResponse)
async def assign_subgroup(
    group_id: UUID,
    request: schemas.AssignSubgroupRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Массовое назначение подгруппы по списку ФИО."""
    result = await db.execute(
        select(models.User).where(
            models.User.group_id == group_id,
            models.User.role == models.UserRole.STUDENT
        )
    )
    students = list(result.scalars().all())
    
    if not students:
        raise HTTPException(status_code=404, detail="No students in group")
    
    input_names = [name.strip() for name in request.names if name.strip()]
    
    matched_students = []
    not_found = []
    
    for input_name in input_names:
        found = False
        for student in students:
            if fio_matches(input_name, student.full_name):
                student.subgroup = request.subgroup
                matched_students.append(student.full_name)
                found = True
                break
        if not found:
            not_found.append(input_name)
    
    try:
        await db.commit()
        return schemas.AssignSubgroupResponse(
            matched=len(matched_students),
            updated_students=matched_students,
            not_found=not_found
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Error assigning subgroups: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@router.post("/{group_id}/clear-subgroups", response_model=schemas.ClearSubgroupsResponse)
async def clear_subgroups(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Убрать подгруппы у всех студентов группы."""
    result = await db.execute(
        select(models.User).where(
            models.User.group_id == group_id,
            models.User.role == models.UserRole.STUDENT
        )
    )
    students = list(result.scalars().all())
    
    count = 0
    for student in students:
        if student.subgroup is not None:
            student.subgroup = None
            count += 1
    
    try:
        await db.commit()
        return schemas.ClearSubgroupsResponse(cleared=count)
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Error clearing subgroups: {e}")
        raise HTTPException(status_code=500, detail="Database error")
