"""Admin impersonate endpoint - login as any user for testing."""
import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_superuser, get_db, get_token_from_cookie
from app.audit.middleware import SESSION_COOKIE_NAME
from app.core import error_messages as em
from app.core import security
from app.core.config import settings
from app.models import User, UserRole
from app.services import session_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Impersonation token TTL (shorter than regular for security)
IMPERSONATE_TOKEN_TTL_MINUTES = 15
ADMIN_TOKEN_COOKIE = "admin_original_token"


@router.post("/impersonate/exit")
async def exit_impersonation(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Return to admin's original session.
    Restores the saved admin token after validation.
    """
    import jwt
    from jwt.exceptions import InvalidTokenError

    original_token = request.cookies.get(ADMIN_TOKEN_COOKIE)

    if not original_token:
        raise HTTPException(
            status_code=400,
            detail=em.INVALID_ADMIN_TOKEN
        )

    # Валидируем original_token и проверяем что это действительно админ
    try:
        payload = jwt.decode(original_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        admin_id = payload.get("sub")
        admin_role = payload.get("role")

        if not admin_id or admin_role != "admin":
            raise HTTPException(status_code=403, detail=em.INVALID_ADMIN_TOKEN)

        # Проверяем что админ существует и активен
        result = await db.execute(select(User).where(User.id == UUID(admin_id)))
        admin_user = result.scalar_one_or_none()

        if not admin_user or not admin_user.is_active or admin_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail=em.ACCESS_FORBIDDEN)

    except InvalidTokenError:
        response.delete_cookie(key=ADMIN_TOKEN_COOKIE)
        raise HTTPException(status_code=401, detail=em.INVALID_ADMIN_TOKEN)

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

    # Clear impersonation flag
    response.delete_cookie(key="impersonating")

    return {"message": "Returned to admin session"}


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
        raise HTTPException(status_code=404, detail=em.USER_NOT_FOUND)

    if not target_user.is_active:
        raise HTTPException(status_code=400, detail=em.ACCESS_FORBIDDEN)

    # Don't allow impersonating other admins
    if target_user.role == UserRole.ADMIN and target_user.id != admin.id:
        raise HTTPException(status_code=403, detail=em.ACCESS_FORBIDDEN)

    is_production = settings.ENVIRONMENT == "production"

    # Save admin's original token for return (HttpOnly for security)
    original_token = get_token_from_cookie(request)
    if original_token:
        response.set_cookie(
            key=ADMIN_TOKEN_COOKIE,
            value=original_token,
            httponly=True,  # Защита от XSS
            secure=is_production,
            samesite="lax",
            max_age=IMPERSONATE_TOKEN_TTL_MINUTES * 60,
            path="/",
        )

    # Set flag cookie for frontend to detect impersonation (non-sensitive)
    response.set_cookie(
        key="impersonating",
        value="true",
        httponly=False,  # JS может читать для UI
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

    # Create impersonation session (doesn't count against user's limit)
    session_id = str(uuid4())
    await session_service.create_session(
        user_id=target_user.id,
        session_id=session_id,
        device_fingerprint=request.headers.get("X-Device-Fingerprint"),
        ip_address=request.client.host if request.client else None,
        is_impersonation=True,
    )

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
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


@router.post("/impersonate/sessions/revoke-all-students")
async def revoke_all_student_sessions(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser),
):
    """
    Выкинуть всех студентов из всех сессий.
    Полезно для очистки сессий на общих компьютерах.
    """
    from app.models.user import UserRole

    # Получаем всех студентов
    result = await db.execute(
        select(User.id).where(User.role == UserRole.STUDENT)
    )
    student_ids = [row[0] for row in result.fetchall()]

    total_revoked = 0
    for student_id in student_ids:
        count = await session_service.revoke_all_user_sessions(student_id)
        total_revoked += count

    logger.warning(
        f"Admin {admin.id} ({admin.full_name}) revoked all student sessions: "
        f"{total_revoked} sessions for {len(student_ids)} students"
    )

    return {
        "message": f"Revoked {total_revoked} sessions for {len(student_ids)} students",
        "students_count": len(student_ids),
        "sessions_revoked": total_revoked
    }
