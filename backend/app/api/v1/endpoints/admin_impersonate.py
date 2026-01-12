"""Admin impersonate endpoint - login as any user for testing."""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_superuser
from app.core import security
from app.core.config import settings
from app.models import User, UserRole

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/impersonate/{user_id}")
async def impersonate_user(
    user_id: UUID,
    response: Response,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    """
    Login as another user (admin only).
    Creates a regular token for the target user - completely invisible to them.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not target_user.is_active:
        raise HTTPException(status_code=400, detail="User is inactive")
    
    # Don't allow impersonating other admins
    if target_user.role == UserRole.ADMIN and target_user.id != admin.id:
        raise HTTPException(status_code=403, detail="Cannot impersonate other admins")
    
    # Create regular token for target user
    access_token = security.create_access_token(target_user.id, role=target_user.role.value)
    
    is_production = settings.ENVIRONMENT == "production"
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    logger.warning(
        f"Admin {admin.id} ({admin.full_name}) impersonated user {target_user.id} ({target_user.full_name})"
    )
    
    return {
        "message": "Impersonation successful",
        "user": {
            "id": str(target_user.id),
            "full_name": target_user.full_name,
            "role": target_user.role.value,
        }
    }
