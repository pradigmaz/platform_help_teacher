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
from app.db.session import get_db
from app.models import User, UserRole # Import UserRole

logger = logging.getLogger(__name__)

# Функция для извлечения токена из куки
def get_token_from_cookie(request: Request) -> Optional[str]:
    return request.cookies.get("access_token")

async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    token = get_token_from_cookie(request)
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
        
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
        
    # FIX: Security check for deactivated users
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    return user

async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    # FIX: Use Enum instead of hardcoded string
    if current_user.role != UserRole.ADMIN: 
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="The user doesn't have enough privileges"
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
         raise HTTPException(status_code=403, detail="Access forbidden")

    try:
        real_ip = ipaddress.ip_address(real_ip_str)

        # Проверка подсетей Telegram
        is_allowed = any(real_ip in ipaddress.ip_network(subnet) for subnet in TELEGRAM_SUBNETS)
        if not is_allowed:
            logger.warning(f"Unauthorized Webhook IP: {real_ip_str} (Client: {client_host})")
            raise HTTPException(status_code=403, detail="Access forbidden")
            
    except ValueError:
        logger.warning(f"Invalid IP address format: {real_ip_str}")
        raise HTTPException(status_code=403, detail="Access forbidden")


async def get_current_teacher(
    current_user: User = Depends(get_current_user),
) -> User:
    """Проверка, что пользователь - преподаватель или админ."""
    if current_user.role not in (UserRole.TEACHER, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only teachers can access this resource"
        )
    return current_user
