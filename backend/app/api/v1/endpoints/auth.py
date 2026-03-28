import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi_csrf_protect import CsrfProtect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import ActionType, EntityType, audit_action
from app.audit.deps import set_audit_extra
from app.audit.middleware import SESSION_COOKIE_NAME
from app.core import error_messages as em
from app.core import security
from app.core.client_ip import extract_client_ip
from app.core.config import settings
from app.core.limiter import limiter
from app.core.redis import get_redis
from app.db.session import get_db
from app.models import User
from app.models.user import UserRole
from app.services import device_service, session_service

router = APIRouter()
logger = logging.getLogger(__name__)
DEV_LOGIN_USERNAME = "dev-local-admin"
DEV_LOGIN_FULL_NAME = "Dev Local Admin"


async def _complete_login(
    *,
    request: Request,
    response: Response,
    user: User,
    remember_device: bool,
    force_session_cookie: bool = False,
    db: AsyncSession,
) -> dict[str, Any]:
    access_token = security.create_access_token(user.id, role=user.role.value)

    is_production = settings.ENVIRONMENT == "production"

    # Для студентов: session cookie по умолчанию (умирает при закрытии браузера)
    # Для admin/teacher: всегда persistent cookie
    # remember_device=True: persistent cookie для всех
    use_persistent_cookie = (
        False if force_session_cookie else user.role in (UserRole.ADMIN, UserRole.TEACHER) or remember_device
    )
    cookie_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60 if use_persistent_cookie else None

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=cookie_max_age,
    )

    session_id = str(uuid4())
    device_fingerprint = request.headers.get("X-Device-Fingerprint")
    client_ip = extract_client_ip(request).value
    await session_service.create_session(
        user_id=user.id,
        session_id=session_id,
        device_fingerprint=device_fingerprint,
        ip_address=client_ip,
    )

    device_registered = await device_service.register_or_update_device(
        db=db,
        user_id=user.id,
        device_fingerprint=device_fingerprint,
    )

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=cookie_max_age,
    )

    return {
        "message": "Logged in successfully",
        "user": {"id": str(user.id), "full_name": user.full_name, "username": user.username, "role": user.role},
        "device_registered": device_registered,
    }


@router.get("/csrf-token")
async def get_csrf_token(csrf_protect: CsrfProtect = Depends()):
    """Get CSRF token for frontend."""
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    response = JSONResponse(content={"csrf_token": csrf_token})
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response


@router.get("/fingerprint-mode")
async def get_fingerprint_mode() -> dict[str, str]:
    """Expose the frontend fingerprint rollout mode for client-side prewarm."""
    return {"mode": settings.FRONTEND_FINGERPRINT_MODE}


@router.post("/otp")
@limiter.limit("5/minute")
@audit_action(ActionType.AUTH_LOGIN, EntityType.AUTH)
async def login_with_otp(
    request: Request,
    response: Response,
    otp: str = Body(...),
    remember_device: bool = Body(False),
    force_session_cookie: bool = Body(False),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    csrf_protect: CsrfProtect = Depends(),
) -> Any:
    """
    Обмен OTP кода на HttpOnly Cookie.
    Поддерживает Telegram и VK.
    """
    await csrf_protect.validate_csrf(request)

    # Логируем для отладки (маскируем код)
    otp_masked = otp[:2] + "****" if len(otp) >= 2 else "***"
    logger.info("OTP login attempt received | code=%s | len=%s", otp_masked, len(otp))

    auth_data = await redis.get(f"auth:{otp}")

    if not auth_data:
        logger.warning("OTP not found in Redis | code=%s", otp_masked)
        raise HTTPException(status_code=400, detail=em.INVALID_OR_EXPIRED_CODE)

    # Парсим данные (JSON с social_id и platform)
    import json

    try:
        data = json.loads(auth_data)
        social_id = data.get("social_id")
        platform = data.get("platform", "telegram")
    except (json.JSONDecodeError, TypeError):
        await redis.delete(f"auth:{otp}")
        raise HTTPException(status_code=400, detail=em.INVALID_DATA_FORMAT)

    await redis.delete(f"auth:{otp}")

    # Добавляем OTP в audit extra_data для связи с BOT_AUTH
    set_audit_extra(request, "otp_used", otp[:3] + "***")  # Маскируем для безопасности
    set_audit_extra(request, "auth_platform", platform)

    # Поиск пользователя по platform
    if platform == "telegram":
        result = await db.execute(select(User).where(User.telegram_id == social_id))
    else:
        result = await db.execute(select(User).where(User.vk_id == social_id))

    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail=em.USER_NOT_FOUND)

    if not user.is_active:
        raise HTTPException(status_code=403, detail=em.ACCESS_FORBIDDEN)

    return await _complete_login(
        request=request,
        response=response,
        user=user,
        remember_device=remember_device,
        force_session_cookie=force_session_cookie,
        db=db,
    )


@router.post("/dev-login")
@limiter.limit("10/minute")
@audit_action(ActionType.AUTH_LOGIN, EntityType.AUTH)
async def login_with_dev_account(
    request: Request,
    response: Response,
    remember_device: bool = Body(True, embed=True),
    db: AsyncSession = Depends(get_db),
    csrf_protect: CsrfProtect = Depends(),
) -> Any:
    """
    Development-only shortcut login.
    WARNING: Must remain unavailable outside local development.
    """
    if settings.ENVIRONMENT != "development":
        raise HTTPException(status_code=404, detail="Not found")

    await csrf_protect.validate_csrf(request)

    set_audit_extra(request, "auth_method", "dev_login")

    result = await db.execute(select(User).where(User.username == DEV_LOGIN_USERNAME))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            full_name=DEV_LOGIN_FULL_NAME,
            username=DEV_LOGIN_USERNAME,
            role=UserRole.ADMIN,
            is_active=True,
            onboarding_completed=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info("Created development login user %s", DEV_LOGIN_USERNAME)
    else:
        changed = False
        if user.role != UserRole.ADMIN:
            user.role = UserRole.ADMIN
            changed = True
        if not user.is_active:
            user.is_active = True
            changed = True
        if not user.onboarding_completed:
            user.onboarding_completed = True
            changed = True
        if changed:
            db.add(user)
            await db.commit()
            await db.refresh(user)

    return await _complete_login(
        request=request,
        response=response,
        user=user,
        remember_device=remember_device,
        db=db,
    )


@router.post("/logout")
@audit_action(ActionType.AUTH_LOGOUT, EntityType.AUTH)
async def logout(request: Request, response: Response):
    # Revoke session in Redis
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        await session_service.revoke_session(session_id)

    is_production = settings.ENVIRONMENT == "production"

    # Удаляем cookies с теми же параметрами, что и при создании
    response.delete_cookie(key="access_token", httponly=True, samesite="lax", secure=is_production, path="/")
    response.delete_cookie(key=SESSION_COOKIE_NAME, httponly=True, samesite="lax", secure=is_production, path="/")
    return {"message": "Logged out"}
