"""
Security Monitor Middleware — детекция атак в реальном времени.
"""
import json
import logging
from typing import Optional, Dict, Any
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.services.security_monitor import get_security_detector, StrikeLevel
from app.services.security_monitor.constants import MESSAGES_RU

logger = logging.getLogger(__name__)


class SecurityMonitorMiddleware(BaseHTTPMiddleware):
    """
    Middleware для детекции SQL injection, XSS, IDOR и других атак.
    
    Логика "3 страйка":
    1. WARNING — header X-Security-Warning
    2. RECORDED — header + запись в БД
    3. BANNED — блокировка 403
    """
    
    # Пути, которые не проверяем
    SKIP_PATHS = {"/health", "/metrics", "/docs", "/openapi.json", "/redoc"}
    
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        
        # Пропускаем служебные эндпоинты
        if path in self.SKIP_PATHS or path.startswith("/static"):
            return await call_next(request)
        
        ip = self._get_client_ip(request)
        if not ip:
            return await call_next(request)
        
        user_id = self._get_user_id_from_token(request)
        fingerprint = self._get_fingerprint(request)
        detector = get_security_detector()
        
        # Собираем URL с query params
        full_url = str(request.url)
        
        # Читаем body для POST/PUT/PATCH (осторожно с размером)
        body = None
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body_bytes = await request.body()
                if len(body_bytes) < 10000:  # Только маленькие body
                    body = body_bytes.decode("utf-8", errors="ignore")
            except Exception:
                pass
        
        try:
            # Проверяем ДО выполнения запроса
            result = await detector.check_and_record(
                ip_address=ip,
                url=full_url,
                user_id=user_id,
                body=body,
                fingerprint=fingerprint,
            )
            
            # Если забанен — сразу 403
            if result.strike_level == StrikeLevel.BANNED:
                return self._banned_response(result)
            
            # Выполняем запрос
            response = await call_next(request)
            
            # Проверяем ПОСЛЕ (для детекции IDOR по 404)
            if response.status_code == 404:
                post_result = await detector.check_and_record(
                    ip_address=ip,
                    url=full_url,
                    user_id=user_id,
                    response_status=404,
                    fingerprint=fingerprint,
                )
                if post_result.is_suspicious:
                    result = post_result
            
            # Добавляем headers если есть предупреждение (без русского текста)
            if result.is_suspicious and result.strike_level != StrikeLevel.NONE:
                response.headers["X-Security-Warning"] = result.strike_level.value
                response.headers["X-Security-Strike"] = str(result.strike_count)
            
            return response
            
        except Exception as e:
            if "greenlet_spawn" not in str(e):
                logger.error(f"SecurityMonitorMiddleware error: {e}")
            return await call_next(request)
    
    def _banned_response(self, result) -> JSONResponse:
        """Формирует ответ для забаненного пользователя."""
        # Русское сообщение для JSON body
        message_ru = MESSAGES_RU.get(StrikeLevel.BANNED, result.message)
        return JSONResponse(
            status_code=403,
            content={
                "detail": message_ru or "Доступ заблокирован",
                "reason": "security_ban",
                "attack_type": result.attack_type.value if result.attack_type else None,
                "ban_until": result.ban_until.isoformat() if result.ban_until else None,
                "strike_count": result.strike_count,
            },
            headers={
                "X-Security-Warning": "banned",
                "X-Security-Strike": str(result.strike_count),
            }
        )
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Получает реальный IP клиента."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        if request.client:
            return request.client.host
        
        return None
    
    def _get_user_id_from_token(self, request: Request) -> Optional[UUID]:
        """Извлекает user_id из JWT."""
        token = request.cookies.get("access_token")
        if not token:
            return None
        
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            user_id_str = payload.get("sub")
            if user_id_str:
                return UUID(user_id_str)
        except (InvalidTokenError, ValueError):
            pass
        
        return None
    
    def _get_fingerprint(self, request: Request) -> Optional[Dict[str, Any]]:
        """Извлекает fingerprint из заголовка."""
        fp_header = request.headers.get("X-Device-Fingerprint")
        if not fp_header:
            return None
        
        try:
            return json.loads(fp_header)
        except (json.JSONDecodeError, TypeError):
            return None
