"""
Admin API для управления rate limit банами.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_superuser
from app.models.user import User
from app.services.rate_limit.admin import (
    get_active_bans,
    get_warnings_history,
    unban_by_warning_id,
    unban_by_user_id,
)
from app.services.rate_limit.schemas import (
    WarningListResponse,
    UnbanRequest,
    UnbanResponse,
)

router = APIRouter()


@router.get("/bans", response_model=WarningListResponse)
async def list_active_bans(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_superuser),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Получить список активных банов."""
    return await get_active_bans(db, skip, limit)


@router.get("/history", response_model=WarningListResponse)
async def list_warnings_history(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_superuser),
    user_id: Optional[UUID] = Query(None),
    ip_address: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Получить историю предупреждений."""
    return await get_warnings_history(db, user_id, ip_address, skip, limit)


@router.post("/unban/{warning_id}", response_model=UnbanResponse)
async def unban_warning(
    warning_id: UUID,
    request: UnbanRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    """Разбанить по ID предупреждения."""
    success = await unban_by_warning_id(db, warning_id, admin.id, request.reason)
    
    if not success:
        raise HTTPException(status_code=404, detail="Warning not found")
    
    return UnbanResponse(
        success=True,
        message="Пользователь разбанен",
        warning_id=warning_id,
    )


@router.post("/unban/user/{user_id}", response_model=UnbanResponse)
async def unban_user(
    user_id: UUID,
    request: UnbanRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    """Разбанить все активные баны пользователя."""
    count = await unban_by_user_id(db, user_id, admin.id, request.reason)
    
    return UnbanResponse(
        success=True,
        message=f"Снято {count} банов",
        warning_id=user_id,  # Используем user_id как идентификатор
    )
