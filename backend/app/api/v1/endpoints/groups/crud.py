"""Group CRUD operations: list, get, create, delete, parse."""
import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models, schemas
from app.api import deps
from app.core import error_messages as em
from app.core.config import settings
from app.core.limiter import limiter
from app.db.session import get_db
from app.services.group_service import GroupService
from app.services.import_service import SmartImportService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=list[schemas.GroupResponse])
async def read_groups(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    include_archived: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Получить список всех групп."""
    query = (
        select(models.Group, func.count(models.User.id).label("students_count"))
        .outerjoin(models.User, models.User.group_id == models.Group.id)
        .group_by(models.Group.id)
        .order_by(models.Group.name)
        .offset(skip)
        .limit(limit)
    )

    if not include_archived:
        query = query.where(not models.Group.is_archived)

    result = await db.execute(query)
    groups = []
    for group, count in result:
        group_data = schemas.GroupResponse.model_validate(group)
        group_data.students_count = count
        groups.append(group_data)
    return groups


@router.post("/", response_model=schemas.GroupResponse)
@limiter.limit("10/minute")
async def create_group(
    request: Request,
    group_in: schemas.GroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Создать новую группу."""
    service = GroupService(db)
    group = await service.create_with_students(group_in)

    group_resp = schemas.GroupResponse.model_validate(group)
    group_resp.students_count = len(group_in.students) if group_in.students else 0
    return group_resp


@router.get("/{group_id}", response_model=schemas.GroupDetailResponse)
async def read_group(
    group_id: UUID,
    active_only: bool = Query(default=True, description="Только активные студенты"),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_teacher),
) -> Any:
    """Детали группы."""
    query = (
        select(models.Group)
        .options(selectinload(models.Group.users))
        .where(models.Group.id == group_id)
    )
    result = await db.execute(query)
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=404, detail=em.GROUP_NOT_FOUND)

    students = group.users
    if active_only:
        students = [u for u in students if u.is_active]
    students = sorted(students, key=lambda u: u.full_name)

    return {
        "id": group.id,
        "name": group.name,
        "code": group.code,
        "invite_code": group.invite_code,
        "created_at": group.created_at,
        "students": students,
        "labs_count": group.labs_count,
        "grading_scale": group.grading_scale,
        "default_max_grade": group.default_max_grade,
    }


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def delete_group(
    request: Request,
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> None:
    """Архивировать группу (soft-delete)."""
    result = await db.execute(select(models.Group).where(models.Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail=em.GROUP_NOT_FOUND)

    try:
        group.is_archived = True
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=500, detail=em.DATABASE_ERROR)


@router.post("/parse", response_model=list[schemas.StudentImport])
async def parse_students_file(
    file: UploadFile = File(...),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Парсинг файла."""
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    if size > settings.MAX_IMPORT_FILE_SIZE:
        raise HTTPException(status_code=400, detail=em.format_error(em.FILE_TOO_LARGE, max="5MB"))

    return await SmartImportService.parse_file(file)
