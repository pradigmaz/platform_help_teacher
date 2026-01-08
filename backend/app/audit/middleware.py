"""
Middleware для автоматического сбора аудит-данных.
"""
import asyncio
import time
import logging
from uuid import uuid4, UUID
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import settings
from .schemas import AuditContext
from .service import get_audit_service
from .utils import extract_ip_info, should_audit, extract_fingerprint
from .constants import ActionType

logger = logging.getLogger(__name__)

# Cookie name for session tracking
SESSION_COOKIE_NAME = "audit_session_id"

# Header for correlation ID (frontend can pass it)
CORRELATION_HEADER = "X-Correlation-ID"


def extract_user_info_from_token(request: Request) -> tuple[Optional[UUID], Optional[str]]:
    """
    Извлечь user_id и role из JWT токена в cookie.
    Returns: (user_id, role) tuple
    """
    token = request.cookies.get("access_token")
    if not token:
        return None, None
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str = payload.get("sub")
        role = payload.get("role")  # Expecting role in JWT payload
        user_id = UUID(user_id_str) if user_id_str else None
        return user_id, role
    except (InvalidTokenError, ValueError):
        pass
    
    return None, None


def extract_session_id(request: Request) -> Optional[str]:
    """Извлечь session_id из cookie."""
    return request.cookies.get(SESSION_COOKIE_NAME)


def extract_correlation_id(request: Request) -> Optional[str]:
    """Извлечь correlation_id из header или сгенерировать."""
    return request.headers.get(CORRELATION_HEADER)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware для сбора базовой информации о запросах.
    
    Логирует только действия студентов в основной лог.
    Действия преподавателей/админов логируются отдельно (admin paths).
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Проверяем, нужно ли логировать этот путь
        if not should_audit(request.url.path):
            return await call_next(request)
        
        # Генерируем request_id
        request_id = str(uuid4())
        
        # Извлекаем IP информацию
        ip_info = extract_ip_info(request)
        
        # Извлекаем fingerprint
        fingerprint = extract_fingerprint(request)
        
        # Извлекаем user_id и role из токена
        user_id, role = extract_user_info_from_token(request)
        
        # Извлекаем session_id из cookie
        session_id = extract_session_id(request)
        
        # Извлекаем correlation_id из header
        correlation_id = extract_correlation_id(request)
        
        # Определяем, нужно ли логировать этого пользователя
        # Логируем только студентов (или неавторизованных)
        # Преподы/админы логируются только для security-critical paths
        is_admin_path = request.url.path.startswith("/api/v1/admin/")
        is_student = role is None or role == "student"
        
        # Пропускаем логирование для преподов на обычных путях
        if not is_student and not is_admin_path:
            # Всё равно выполняем запрос, просто не логируем
            return await call_next(request)
        
        # Создаём контекст аудита
        audit_context = AuditContext(
            request_id=request_id,
            correlation_id=correlation_id,
            user_id=user_id,
            session_id=session_id,
            actor_role=role or "anonymous",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params) if request.query_params else None,
            ip_address=ip_info.real_ip,
            ip_forwarded=ip_info.forwarded_chain,
            user_agent=request.headers.get("user-agent"),
            fingerprint=fingerprint,
            action_type=self._infer_action_type(request.method),
        )
        
        # Сохраняем в request.state для доступа из endpoints
        request.state.audit_context = audit_context
        request.state.audit_request_id = request_id
        
        # Засекаем время
        start_time = time.perf_counter()
        
        # Выполняем запрос
        response = await call_next(request)
        
        # Дополняем контекст
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        audit_context.response_status = response.status_code
        audit_context.duration_ms = duration_ms
        
        # Определяем action_type по статусу
        if response.status_code >= 400:
            audit_context.action_type = ActionType.ERROR.value
        
        # Выбираем метод записи в зависимости от критичности
        audit_service = get_audit_service()
        if audit_service.is_security_critical(audit_context.action_type):
            # Синхронная запись с retry для security-critical
            await audit_service.write_log_sync(audit_context)
        else:
            # Асинхронная запись (fire-and-forget) для остальных
            asyncio.create_task(audit_service.write_log(audit_context))
        
        return response
    
    def _infer_action_type(self, method: str) -> str:
        """Определить тип действия по HTTP методу."""
        method_map = {
            "GET": ActionType.VIEW.value,
            "POST": ActionType.CREATE.value,
            "PUT": ActionType.UPDATE.value,
            "PATCH": ActionType.UPDATE.value,
            "DELETE": ActionType.DELETE.value,
        }
        return method_map.get(method, ActionType.VIEW.value)
