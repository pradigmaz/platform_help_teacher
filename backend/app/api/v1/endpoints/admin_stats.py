from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.session import get_db
from app.models import User, Group
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

    return {
        "total_users": total_users,
        "total_groups": total_groups,
        "total_students": total_students,
        "active_labs": 0,
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


@router.post("/students/{student_id}/reset-telegram")
async def reset_student_telegram(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Сбросить привязку Telegram у студента."""
    result = await db.execute(select(User).where(User.id == student_id))
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student.social_id = None
    await db.commit()
    
    return {"status": "success", "message": "Telegram отвязан"}
