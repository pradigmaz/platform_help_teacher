from datetime import datetime, timedelta, timezone
from typing import Union, Optional
from uuid import UUID
import jwt  # PyJWT
from app.core.config import settings


def create_access_token(
    user_id: Union[str, UUID], 
    role: Optional[str] = None,
    expires_minutes: Optional[int] = None,
    impersonated_by: Optional[Union[str, UUID]] = None,
) -> str:
    """Создает JWT токен для пользователя с ролью.
    
    Args:
        user_id: ID пользователя
        role: Роль пользователя
        expires_minutes: Время жизни токена (по умолчанию из настроек)
        impersonated_by: ID админа, если это impersonation-токен
    """
    ttl = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=ttl)
    
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
    }
    
    if role:
        to_encode["role"] = role
    
    if impersonated_by:
        to_encode["impersonated_by"] = str(impersonated_by)
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt