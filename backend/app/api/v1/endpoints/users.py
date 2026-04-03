import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.api import deps
from app.core.limiter import limiter
from app.db.session import get_db
from app.schemas.user import (
    ContactVisibilitySettings,
    RelinkTelegramResponse,
    TeacherContacts,
    TeacherContactsResponse,
    TeacherContactsUpdate,
)
from app.services.user_service import user_service

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
    logger.info(
        "[users:create_user] Admin %s creating user telegram_id=%s vk_id=%s",
        current_user.id,
        user_in.telegram_id,
        user_in.vk_id,
    )
    return await user_service.create_user(db, user_in)


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
    Update current user (onboarding_completed only).
    SECURITY: full_name change is forbidden for students.
    """
    logger.info(f"[users:update_user_me] User {current_user.id} updating profile")

    # Students cannot change their full_name
    if user_in.full_name is not None and current_user.role == models.UserRole.STUDENT:
        logger.warning(f"[users:update_user_me] Student {current_user.id} attempted to change full_name")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Students cannot change their name")

    return await user_service.update_user(db, current_user, user_in)


@router.post("/me/relink-telegram", response_model=RelinkTelegramResponse)
@limiter.limit("5/hour")
async def relink_telegram(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> RelinkTelegramResponse:
    """
    Получить код для перепривязки Telegram.
    Работает для всех ролей: студент, преподаватель, админ.

    SECURITY: Код привязан к текущему telegram_id пользователя.
    Если у пользователя уже есть привязка, код может использовать только он.
    """
    from app.services import bot_service

    code = await bot_service.generate_relink_code(
        db, current_user.id, "telegram", current_social_id=current_user.telegram_id
    )

    return RelinkTelegramResponse(
        code=code,
        expires_in=bot_service.RELINK_TTL,
    )


@router.post("/me/link-vk", response_model=RelinkTelegramResponse)
@limiter.limit("5/hour")
async def link_vk(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> RelinkTelegramResponse:
    """
    Получить код для привязки VK.
    Работает для всех ролей: студент, преподаватель, админ.

    SECURITY: Код привязан к текущему vk_id пользователя.
    Если у пользователя уже есть привязка, код может использовать только он.
    """
    from app.services import bot_service

    code = await bot_service.generate_relink_code(db, current_user.id, "vk", current_social_id=current_user.vk_id)

    return RelinkTelegramResponse(
        code=code,
        expires_in=bot_service.RELINK_TTL,
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
    logger.info(f"[users:update_my_contacts] Teacher {current_user.id} updating contacts")

    updated_user = await user_service.update_contacts(db, current_user, data)

    return TeacherContactsResponse(
        contacts=TeacherContacts(**updated_user.contacts),
        visibility=ContactVisibilitySettings(**updated_user.contact_visibility),
    )


# ============ Teacher Settings Endpoints ============


class TeacherSettingsResponse(BaseModel):
    hide_previous_semester: bool = True


class TeacherSettingsUpdate(BaseModel):
    hide_previous_semester: bool | None = None


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
    logger.info(f"[users:update_my_settings] Teacher {current_user.id} updating settings")

    updated_user = await user_service.update_settings(
        db, current_user, hide_previous_semester=data.hide_previous_semester
    )

    settings = updated_user.teacher_settings or {}
    return TeacherSettingsResponse(
        hide_previous_semester=settings.get("hide_previous_semester", True),
    )
