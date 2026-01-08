from datetime import datetime, timedelta, timezone
from typing import Union, Optional
from uuid import UUID
import jwt  # PyJWT
from app.core.config import settings


def create_access_token(user_id: Union[str, UUID], role: Optional[str] = None) -> str:
    """Создает JWT токен для пользователя с ролью."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
    }
    
    if role:
        to_encode["role"] = role
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt