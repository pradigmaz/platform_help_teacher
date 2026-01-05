from typing import Any, List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api import deps
from app.db.session import get_db
from app.core.limiter import limiter
from app.models import User, Lab, LabSettings
from app import schemas

router = APIRouter()

class LabCreate(BaseModel):
    title: str
    description: Optional[str] = None
    max_grade: int = 10
    deadline: Optional[datetime] = None

class LabUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    max_grade: Optional[int] = None
    deadline: Optional[datetime] = None

class LabOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    max_grade: int
    deadline: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

@router.get("/labs", response_model=List[LabOut])
async def get_all_labs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить все лабораторные работы."""
    result = await db.execute(select(Lab).order_by(Lab.created_at.desc()))
    labs = result.scalars().all()
    return labs

@router.post("/labs", response_model=LabOut)
@limiter.limit("15/minute")
async def create_lab(
    request: Request,
    lab_in: LabCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Создать лабораторную работу."""
    lab = Lab(
        title=lab_in.title,
        description=lab_in.description,
        max_grade=lab_in.max_grade,
        deadline=lab_in.deadline,
    )
    db.add(lab)
    await db.commit()
    await db.refresh(lab)
    return lab

@router.patch("/labs/{lab_id}", response_model=LabOut)
async def update_lab(
    lab_id: UUID,
    lab_in: LabUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Обновить лабораторную работу."""
    result = await db.execute(select(Lab).where(Lab.id == lab_id))
    lab = result.scalar_one_or_none()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    
    update_data = lab_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lab, field, value)
    
    await db.commit()
    await db.refresh(lab)
    return lab

@router.delete("/labs/{lab_id}", response_model=schemas.DeleteResponse)
@limiter.limit("10/minute")
async def delete_lab(
    request: Request,
    lab_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> schemas.DeleteResponse:
    """Удалить лабораторную работу."""
    result = await db.execute(select(Lab).where(Lab.id == lab_id))
    lab = result.scalar_one_or_none()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    
    await db.delete(lab)
    await db.commit()
    return {"status": "deleted"}


# --- Global Lab Settings ---

@router.get("/lab-settings", response_model=schemas.LabSettingsResponse)
async def get_lab_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить глобальные настройки лабораторных."""
    result = await db.execute(select(LabSettings).limit(1))
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Создаём настройки по умолчанию
        settings = LabSettings(labs_count=10, default_max_grade=10)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    
    return settings


@router.patch("/lab-settings", response_model=schemas.LabSettingsResponse)
async def update_lab_settings(
    settings_in: schemas.LabSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Обновить глобальные настройки лабораторных."""
    result = await db.execute(select(LabSettings).limit(1))
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = LabSettings(labs_count=10, default_max_grade=10)
        db.add(settings)
        await db.flush()
    
    update_data = settings_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
    
    await db.commit()
    await db.refresh(settings)
    return settings

