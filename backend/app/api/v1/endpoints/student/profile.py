"""Student profile endpoint."""
from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.group import Group
from app.audit import audit_action, ActionType, EntityType

router = APIRouter()


@router.get("/profile")
@audit_action(ActionType.VIEW, EntityType.PROFILE)
async def get_my_profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Профиль студента с информацией о группе."""
    
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
        "telegram_id": current_user.telegram_id,
        "vk_id": current_user.vk_id,
        "role": current_user.role.value,
        "group": group_info,
    }
