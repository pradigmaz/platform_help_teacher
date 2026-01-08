"""
IP Ban Middleware — временная блокировка IP после множества 429 ошибок.

Защита от brute-force и DDoS атак.
Интегрирован с RateLimitService для мягких предупреждений.
"""
import logging
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.redis import get_redis
from app.services.rate_limit import get_rate_limit_service, WarningLevel
from app.services.rate_limit.constants import MESSAGES

logger = logging.getLogger(__name__)


class IPBanMiddleware(BaseHTTPMiddleware):
    """
    Middleware для rate limit с мягкими предупреждениями.
    
    Логика:
    1. Проверяем, не забанен ли IP/user
    2. Если забанен — возвращаем 403 с сообщением
    3. Если ответ 429 — записываем нарушение
    4. Добавляем warning header если нужно
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        ip = self._get_client_ip(request)
        
        if not ip:
            return await call_next(request)
        
        # Получаем user_id из сессии если есть
        user_id = getattr(request.state, "user_id", None)
        
        service = get_rate_limit_service()
        
        try:
            # Проверяем бан
            ban_info = await service.check_ban(ip, user_id)
            
            if ban_info.is_banned:
                logger.warning(f"Blocked request from banned: ip={ip}, user={user_id}")
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": ban_info.message or "Доступ временно заблокирован",
                        "ban_until": ban_info.ban_until.isoformat() if ban_info.ban_until else None,
                        "warning_level": ban_info.warning_level.value if ban_info.warning_level else None,
                    },
                    headers={"X-Rate-Limit-Warning": ban_info.warning_level.value if ban_info.warning_level else "banned"}
                )
            
            # Выполняем запрос
            response = await call_next(request)
            
            # Обрабатываем 429
            if response.status_code == 429:
                level, message = await service.record_violation(ip, user_id)
                
                if message:
                    # Добавляем header с предупреждением
                    response.headers["X-Rate-Limit-Warning"] = level.value
                    response.headers["X-Rate-Limit-Message"] = message
            
            return response
            
        except Exception as e:
            logger.error(f"IPBanMiddleware error: {e}")
            return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Получает реальный IP клиента с учётом прокси."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        if request.client:
            return request.client.host
        
        return None
