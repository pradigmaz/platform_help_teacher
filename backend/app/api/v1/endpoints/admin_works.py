"""API эндпоинты для управления работами (контрольные, самостоятельные, коллоквиумы, проекты)."""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.api import deps
from app.db.session import get_db
from app.models import User
from app.models.work_type import WorkType
from app.crud.crud_work import work as crud_work

router = APIRouter()


class WorkCreate(BaseModel):
    title: str = Field(..., max_length=200)
    work_type: WorkType
    description: Optional[str] = None
    max_grade: int = Field(default=10, ge=1, le=100)
    deadline: Optional[datetime] = None
    s3_key: Optional[str] = None


class WorkUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    max_grade: Optional[int] = Field(None, ge=1, le=100)
    deadline: Optional[datetime] = None
    s3_key: Optional[str] = None


class WorkResponse(BaseModel):
    id: UUID
    title: str
    work_type: WorkType
    description: Optional[str]
    max_grade: int
    deadline: Optional[datetime]
    s3_key: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("/works", response_model=WorkResponse)
async def create_work(
    work_in: WorkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Создать новую работу."""
    work_obj = await crud_work.create(
        db,
        title=work_in.title,
        work_type=work_in.work_type,
        description=work_in.description,
        max_grade=work_in.max_grade,
        deadline=work_in.deadline,
        s3_key=work_in.s3_key
    )
    return work_obj


@router.get("/works", response_model=List[WorkResponse])
async def get_works(
    work_type: Optional[WorkType] = Query(None, description="Фильтр по типу работы"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить список работ."""
    if work_type:
        works = await crud_work.get_by_type(db, work_type, limit=limit, offset=offset)
    else:
        works = await crud_work.get_all(db, limit=limit, offset=offset)
    return works


@router.get("/works/{work_id}", response_model=WorkResponse)
async def get_work(
    work_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить работу по ID."""
    work_obj = await crud_work.get(db, work_id)
    if not work_obj:
        raise HTTPException(status_code=404, detail="Работа не найдена")
    return work_obj


@router.patch("/works/{work_id}", response_model=WorkResponse)
async def update_work(
    work_id: UUID,
    work_in: WorkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Обновить работу."""
    work_obj = await crud_work.get(db, work_id)
    if not work_obj:
        raise HTTPException(status_code=404, detail="Работа не найдена")
    
    work_obj = await crud_work.update(
        db,
        db_obj=work_obj,
        title=work_in.title,
        description=work_in.description,
        max_grade=work_in.max_grade,
        deadline=work_in.deadline,
        s3_key=work_in.s3_key
    )
    return work_obj


@router.delete("/works/{work_id}")
async def delete_work(
    work_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Удалить работу."""
    deleted = await crud_work.delete(db, id=work_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Работа не найдена")
    return {"status": "deleted"}
