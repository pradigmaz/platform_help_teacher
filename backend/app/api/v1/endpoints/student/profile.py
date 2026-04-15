"""Student profile endpoint."""

from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.audit import ActionType, EntityType, audit_action
from app.models.group import Group
from app.models.user import User

router = APIRouter()


async def build_student_profile(
    db: AsyncSession,
    current_user: User,
) -> dict[str, Any]:
    """Build student profile payload with group info."""
    group_info = None
    if current_user.group_id:
        group = await db.get(Group, current_user.group_id)
        if group:
            group_info = {
                "id": str(group.id),
                "name": group.name,
                "code": group.code,
            }

    return {
        "id": str(current_user.id),
        "full_name": current_user.full_name,
        "username": current_user.username,
        "has_telegram": current_user.telegram_id is not None,
        "has_vk": current_user.vk_id is not None,
        "role": current_user.role.value,
        "group": group_info,
    }


@router.get("/profile")
@audit_action(ActionType.VIEW, EntityType.PROFILE)
async def get_my_profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Профиль студента с информацией о группе."""
    return await build_student_profile(db, current_user)
