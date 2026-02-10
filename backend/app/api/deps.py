from typing import Annotated, Optional
from uuid import UUID
import ipaddress
import logging
from fastapi import Depends, HTTPException, status, Request
import jwt  # PyJWT
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import TELEGRAM_SUBNETS
from app.core import error_messages as em
from app.db.session import get_db
from app.models import User, UserRole # Import UserRole
from app.audit.middleware import SESSION_COOKIE_NAME
from app.services import session_service

logger = logging.getLogger(__name__)

# Функция для извлечения токена из куки
def get_token_from_cookie(request: Request) -> Optional[str]:
    return request.cookies.get("access_token")

async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    token = get_token_from_cookie(request)
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path

    if not token:
        logger.warning(f"Auth failed: no token | path={path} | ip={client_ip}")
        request.state.auth_error_reason = "no_token"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning(f"Auth failed: no 'sub' in token | path={path} | ip={client_ip}")
            request.state.auth_error_reason = "invalid_token_no_sub"
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Track impersonation for audit
        impersonated_by = payload.get("impersonated_by")
        if impersonated_by:
            logger.info(f"Impersonated request: admin={impersonated_by}, acting_as={user_id}, path={path}")
            request.state.impersonated_by = impersonated_by
            
    except jwt.ExpiredSignatureError:
        logger.warning(f"Auth failed: token expired | path={path} | ip={client_ip}")
        request.state.auth_error_reason = "token_expired"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError as e:
        logger.warning(f"Auth failed: invalid token | error={str(e)[:100]} | path={path} | ip={client_ip}")
        request.state.auth_error_reason = "invalid_token"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validate session in Redis
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        session_data = await session_service.validate_session(session_id)
        if not session_data:
            logger.warning(
                f"[deps:get_current_user] Auth failed: session revoked | "
                f"user_id={user_id} | session_id={session_id[:8]}... | path={path} | ip={client_ip}"
            )
            request.state.auth_error_reason = "session_revoked"
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.debug(f"[deps:get_current_user] Session validated | session_id={session_id[:8]}... | user_id={user_id}")
    else:
        # No session cookie - this might be an old token or API access
        # For now, we'll allow it but log a warning
        logger.warning(
            f"[deps:get_current_user] No session cookie found | "
            f"user_id={user_id} | path={path} | ip={client_ip}"
        )
        
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    
    if user is None:
        logger.warning(f"Auth failed: user not found | user_id={user_id} | path={path} | ip={client_ip}")
        request.state.auth_error_reason = "user_not_found"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=em.USER_NOT_FOUND,
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        logger.warning(f"Auth failed: user inactive | user_id={user_id} | path={path} | ip={client_ip}")
        request.state.auth_error_reason = "user_inactive"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user

async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    # FIX: Use Enum instead of hardcoded string
    if current_user.role != UserRole.ADMIN: 
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=em.NOT_ENOUGH_PERMISSIONS
        )
    return current_user

async def verify_telegram_ip(request: Request):
    """
    Проверка, что запрос пришел от Telegram.
    При работе через прокси (Nginx) доверяем X-Forwarded-For,
    если сам запрос пришел из локальной сети (Docker network).
    """
    # В dev-режиме пропускаем проверку IP (для ngrok и локальной разработки)
    if settings.ENVIRONMENT == "development":
        return
    
    client_host = request.client.host if request.client else None
    
    # 1. Попытка получить реальный IP из заголовка X-Forwarded-For
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Берём первый IP из списка (клиентский)
        real_ip_str = forwarded_for.split(",")[0].strip()
    else:
        real_ip_str = client_host

    if not real_ip_str:
         logger.warning("Could not determine client IP")
         raise HTTPException(status_code=403, detail=em.ACCESS_FORBIDDEN)

    try:
        real_ip = ipaddress.ip_address(real_ip_str)

        # Проверка подсетей Telegram
        is_allowed = any(real_ip in ipaddress.ip_network(subnet) for subnet in TELEGRAM_SUBNETS)
        if not is_allowed:
            logger.warning(f"Unauthorized Webhook IP: {real_ip_str} (Client: {client_host})")
            raise HTTPException(status_code=403, detail=em.ACCESS_FORBIDDEN)
            
    except ValueError:
        logger.warning(f"Invalid IP address format: {real_ip_str}")
        raise HTTPException(status_code=403, detail=em.ACCESS_FORBIDDEN)


async def get_current_teacher(
    current_user: User = Depends(get_current_user),
) -> User:
    """Проверка, что пользователь - преподаватель или админ."""
    if current_user.role not in (UserRole.TEACHER, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=em.NOT_ENOUGH_PERMISSIONS
        )
    return current_user
