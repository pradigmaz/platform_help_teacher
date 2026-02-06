from typing import Any
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Response, Body, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_csrf_protect import CsrfProtect

from app.core import security
from app.core.config import settings
from app.core.limiter import limiter
from app.db.session import get_db
from app.core.redis import get_redis
from app.models import User
from app.models.user import UserRole
from app.audit import audit_action, ActionType, EntityType
from app.audit.middleware import SESSION_COOKIE_NAME
from app.audit.deps import set_audit_extra
from app.services import session_service

router = APIRouter()


@router.get("/csrf-token")
async def get_csrf_token(csrf_protect: CsrfProtect = Depends()):
    """Get CSRF token for frontend."""
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    response = JSONResponse(content={"csrf_token": csrf_token})
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response


@router.post("/otp")
@limiter.limit("5/minute")
@audit_action(ActionType.AUTH_LOGIN, EntityType.AUTH)
async def login_with_otp(
    request: Request,
    response: Response,
    otp: str = Body(...),
    remember_device: bool = Body(False),
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
    csrf_protect: CsrfProtect = Depends()
) -> Any:
    """
    Обмен OTP кода на HttpOnly Cookie.
    Поддерживает Telegram и VK.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    await csrf_protect.validate_csrf(request)
    
    # Логируем для отладки (маскируем код)
    otp_masked = otp[:2] + "****" if len(otp) >= 2 else "***"
    logger.info(f"OTP login attempt: code={otp_masked}, len={len(otp)}, repr={repr(otp)}")
    
    auth_data = await redis.get(f"auth:{otp}")
    
    if not auth_data:
        logger.warning(f"OTP not found in Redis: code={otp_masked}")
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    
    # Парсим данные (JSON с social_id и platform)
    import json
    try:
        data = json.loads(auth_data)
        social_id = data.get("social_id")
        platform = data.get("platform", "telegram")
    except (json.JSONDecodeError, TypeError):
        await redis.delete(f"auth:{otp}")
        raise HTTPException(status_code=400, detail="Invalid data format")

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
        raise HTTPException(status_code=404, detail="User not found")
        
    if not user.is_active:
         raise HTTPException(status_code=403, detail="User is inactive")
        
    access_token = security.create_access_token(user.id, role=user.role.value)
    
    is_production = settings.ENVIRONMENT == "production"
    
    # Для студентов: session cookie по умолчанию (умирает при закрытии браузера)
    # Для admin/teacher: всегда persistent cookie
    # remember_device=True: persistent cookie для всех
    use_persistent_cookie = (
        user.role in (UserRole.ADMIN, UserRole.TEACHER) or remember_device
    )
    cookie_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60 if use_persistent_cookie else None
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=cookie_max_age
    )
    
    # Generate session_id for audit tracking and session management
    session_id = str(uuid4())
    
    # Create session in Redis with limit enforcement
    device_fingerprint = request.headers.get("X-Device-Fingerprint")
    client_ip = request.client.host if request.client else None
    await session_service.create_session(
        user_id=user.id,
        session_id=session_id,
        device_fingerprint=device_fingerprint,
        ip_address=client_ip,
    )
    
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=cookie_max_age
    )
    
    return {"message": "Logged in successfully", "user": {"full_name": user.full_name, "role": user.role}}

@router.post("/logout")
@audit_action(ActionType.AUTH_LOGOUT, EntityType.AUTH)
async def logout(request: Request, response: Response):
    # Revoke session in Redis
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        await session_service.revoke_session(session_id)
    
    is_production = settings.ENVIRONMENT == "production"
    
    # Удаляем cookies с теми же параметрами, что и при создании
    response.delete_cookie(
        key="access_token", 
        httponly=True, 
        samesite="lax",
        secure=is_production,
        path="/"
    )
    response.delete_cookie(
        key=SESSION_COOKIE_NAME, 
        httponly=True, 
        samesite="lax",
        secure=is_production,
        path="/"
    )
    return {"message": "Logged out"}