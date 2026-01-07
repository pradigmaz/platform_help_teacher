from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.session import get_db
from app.models import User, Group, Lab
from app.schemas import StudentProfileOut, StatsResponse
from app.services.student_service import StudentService

router = APIRouter()

@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> StatsResponse:
    """
    Получить статистику по платформе (для админ-панели).
    """
    # Считаем количество пользователей
    users_result = await db.execute(select(func.count(User.id)))
    total_users = users_result.scalar() or 0

    # Считаем количество групп
    groups_result = await db.execute(select(func.count(Group.id)))
    total_groups = groups_result.scalar() or 0

    # Считаем активных студентов (у кого есть роль student)
    students_result = await db.execute(select(func.count(User.id)).where(User.role == "student"))
    total_students = students_result.scalar() or 0

    # Считаем количество лабораторных
    labs_result = await db.execute(select(func.count(Lab.id)))
    active_labs = labs_result.scalar() or 0

    return {
        "total_users": total_users,
        "total_groups": total_groups,
        "total_students": total_students,
        "active_labs": active_labs,
        "total_submissions": 0
    }

@router.get("/students/{student_id}", response_model=StudentProfileOut)
async def get_student_profile(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить профиль студента с его лабораторными работами и статистикой."""
    service = StudentService(db)
    profile = await service.get_profile(student_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Student not found")
        
    return profile


@router.post("/students/{student_id}/reset-social")
async def reset_student_social(
    student_id: UUID,
    platform: str = "all",  # "telegram", "vk", or "all"
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Сбросить привязку социальных сетей у студента."""
    result = await db.execute(select(User).where(User.id == student_id))
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if platform in ("telegram", "all"):
        student.telegram_id = None
    if platform in ("vk", "all"):
        student.vk_id = None
    
    await db.commit()
    
    msg = "Все привязки сброшены" if platform == "all" else f"{platform.upper()} отвязан"
    return {"status": "success", "message": msg}


# Обратная совместимость
@router.post("/students/{student_id}/reset-telegram")
async def reset_student_telegram(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Сбросить привязку Telegram у студента (deprecated, use reset-social)."""
    return await reset_student_social(student_id, "telegram", db, current_user)


# --- Transfer endpoints ---
from app.services.transfer_service import TransferService
from app.schemas.transfer import TransferRequest, TransferResponse, StudentTransfersResponse


@router.post("/students/{student_id}/transfer", response_model=TransferResponse)
async def transfer_student(
    student_id: UUID,
    request: TransferRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Перевести студента в другую группу/подгруппу с сохранением снапшота."""
    service = TransferService(db)
    try:
        result = await service.create_transfer(
            student_id=student_id,
            request=request,
            created_by_id=current_user.id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/students/{student_id}/transfers", response_model=StudentTransfersResponse)
async def get_student_transfers(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить историю переводов студента."""
    service = TransferService(db)
    try:
        return await service.get_student_transfers(student_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
