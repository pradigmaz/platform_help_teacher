from typing import Any, Optional
import logging
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app import schemas, models
from app.api import deps
from app.db.session import get_db
from app.core.limiter import limiter
from app.schemas.user import (
    TeacherContactsUpdate,
    TeacherContactsResponse,
    TeacherContacts,
    ContactVisibilitySettings,
    RelinkTelegramResponse,
)
from app.services import telegram_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=schemas.UserResponse)
@limiter.limit("20/minute")
async def create_user(
    request: Request,
    *,
    db: AsyncSession = Depends(get_db),
    user_in: schemas.UserCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new user.
    SECURITY: Only admins can create users manually.
    """
    # 1. Проверка существования
    result = await db.execute(select(models.User).where(models.User.social_id == user_in.social_id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User with this social ID already exists")

    # 2. Поиск группы
    group_id = None
    if user_in.group_code:
        group_res = await db.execute(select(models.Group).where(models.Group.code == user_in.group_code))
        group = group_res.scalar_one_or_none()
        if group:
            group_id = group.id
            
    try:
        # 3. Подготовка объекта
        user = models.User(
            social_id=user_in.social_id,
            full_name=user_in.full_name,
            username=user_in.username,
            role=user_in.role,
            group_id=group_id,
            is_active=True
        )
        db.add(user)
        
        # 4. Фиксация транзакции
        await db.commit()
        await db.refresh(user)
        return user
        
    except SQLAlchemyError as e:
        # FIX: Явный откат при ошибке
        await db.rollback()
        logger.error(f"Error creating user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during user creation"
        )

@router.get("/me", response_model=schemas.UserResponse)
async def read_user_me(
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.patch("/me", response_model=schemas.UserResponse)
async def update_user_me(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Update current user (full_name, onboarding_completed).
    """
    if user_in.full_name is not None:
        current_user.full_name = user_in.full_name
    if user_in.onboarding_completed is not None:
        current_user.onboarding_completed = user_in.onboarding_completed
    
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post("/me/relink-telegram", response_model=RelinkTelegramResponse)
async def relink_telegram(
    current_user: models.User = Depends(deps.get_current_user),
) -> RelinkTelegramResponse:
    """
    Получить код для перепривязки Telegram.
    Работает для всех ролей: студент, преподаватель, админ.
    """
    code = await telegram_service.generate_relink_code(current_user.id)
    
    return RelinkTelegramResponse(
        code=code,
        expires_in=telegram_service.RELINK_TTL,
    )



# ============ Teacher Contacts Endpoints ============

@router.get("/profile/contacts", response_model=TeacherContactsResponse)
async def get_my_contacts(
    current_user: models.User = Depends(deps.get_current_teacher),
) -> TeacherContactsResponse:
    """
    Получить свои контакты (только для преподавателей).
    """
    contacts_data = current_user.contacts or {}
    visibility_data = current_user.contact_visibility or {}
    
    return TeacherContactsResponse(
        contacts=TeacherContacts(**contacts_data),
        visibility=ContactVisibilitySettings(**visibility_data),
    )


@router.put("/profile/contacts", response_model=TeacherContactsResponse)
async def update_my_contacts(
    data: TeacherContactsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_teacher),
) -> TeacherContactsResponse:
    """
    Обновить свои контакты (только для преподавателей).
    """
    current_user.contacts = data.contacts.model_dump(exclude_none=True)
    current_user.contact_visibility = data.visibility.model_dump()
    
    await db.commit()
    await db.refresh(current_user)
    
    return TeacherContactsResponse(
        contacts=TeacherContacts(**current_user.contacts),
        visibility=ContactVisibilitySettings(**current_user.contact_visibility),
    )



# ============ Teacher Settings Endpoints ============

class TeacherSettingsResponse(BaseModel):
    hide_previous_semester: bool = True


class TeacherSettingsUpdate(BaseModel):
    hide_previous_semester: Optional[bool] = None


@router.get("/profile/settings", response_model=TeacherSettingsResponse)
async def get_my_settings(
    current_user: models.User = Depends(deps.get_current_teacher),
) -> TeacherSettingsResponse:
    """
    Получить настройки преподавателя.
    """
    settings = current_user.teacher_settings or {}
    return TeacherSettingsResponse(
        hide_previous_semester=settings.get("hide_previous_semester", True),
    )


@router.put("/profile/settings", response_model=TeacherSettingsResponse)
async def update_my_settings(
    data: TeacherSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_teacher),
) -> TeacherSettingsResponse:
    """
    Обновить настройки преподавателя.
    """
    settings = current_user.teacher_settings or {}
    
    if data.hide_previous_semester is not None:
        settings["hide_previous_semester"] = data.hide_previous_semester
    
    current_user.teacher_settings = settings
    await db.commit()
    await db.refresh(current_user)
    
    return TeacherSettingsResponse(
        hide_previous_semester=settings.get("hide_previous_semester", True),
    )
