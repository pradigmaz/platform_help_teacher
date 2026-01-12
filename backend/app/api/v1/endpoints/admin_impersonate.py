"""Admin impersonate endpoint - login as any user for testing."""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_superuser, get_token_from_cookie
from app.core import security
from app.core.config import settings
from app.models import User, UserRole

logger = logging.getLogger(__name__)
router = APIRouter()

# Impersonation token TTL (shorter than regular for security)
IMPERSONATE_TOKEN_TTL_MINUTES = 15
ADMIN_TOKEN_COOKIE = "admin_original_token"


@router.post("/impersonate/{user_id}")
async def impersonate_user(
    user_id: UUID,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    """
    Login as another user (admin only).
    Saves admin's original token for easy return.
    Creates a short-lived token with impersonation tracking.
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
    
    is_production = settings.ENVIRONMENT == "production"
    
    # Save admin's original token for return
    original_token = get_token_from_cookie(request)
    if original_token:
        response.set_cookie(
            key=ADMIN_TOKEN_COOKIE,
            value=original_token,
            httponly=False,  # Allow JS to detect impersonation
            secure=is_production,
            samesite="lax",
            max_age=IMPERSONATE_TOKEN_TTL_MINUTES * 60,
            path="/",
        )
    
    # Create short-lived token with impersonation tracking
    access_token = security.create_access_token(
        target_user.id, 
        role=target_user.role.value,
        expires_minutes=IMPERSONATE_TOKEN_TTL_MINUTES,
        impersonated_by=admin.id,
    )
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=IMPERSONATE_TOKEN_TTL_MINUTES * 60,
    )
    
    logger.warning(
        f"Admin {admin.id} ({admin.full_name}) impersonated user {target_user.id} ({target_user.full_name})"
    )
    
    return {
        "message": "Impersonation successful",
        "expires_in_minutes": IMPERSONATE_TOKEN_TTL_MINUTES,
        "user": {
            "id": str(target_user.id),
            "full_name": target_user.full_name,
            "role": target_user.role.value,
        }
    }


@router.post("/impersonate/exit")
async def exit_impersonation(
    request: Request,
    response: Response,
):
    """
    Return to admin's original session.
    Restores the saved admin token.
    """
    original_token = request.cookies.get(ADMIN_TOKEN_COOKIE)
    
    if not original_token:
        raise HTTPException(
            status_code=400, 
            detail="No admin session to restore. Please login again."
        )
    
    is_production = settings.ENVIRONMENT == "production"
    
    # Restore admin's original token
    response.set_cookie(
        key="access_token",
        value=original_token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    
    # Clear the backup cookie
    response.delete_cookie(key=ADMIN_TOKEN_COOKIE)
    
    logger.info("Admin exited impersonation mode")
    
    return {"message": "Returned to admin session"}
