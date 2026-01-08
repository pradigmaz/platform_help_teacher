"""
FastAPI dependencies для аудита.
"""
from typing import Optional
from fastapi import Depends, Request

from app.api.deps import get_current_user
from app.models.user import User
from .schemas import AuditContext


async def audit_user(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency для автоматической привязки user_id к аудиту.
    Заменяет get_current_user в endpoints.
    """
    if hasattr(request.state, 'audit_context'):
        request.state.audit_context.user_id = current_user.id
    return current_user


def get_audit_context(request: Request) -> Optional[AuditContext]:
    """Получить контекст аудита из request."""
    return getattr(request.state, 'audit_context', None)


def set_audit_extra(request: Request, key: str, value) -> None:
    """Добавить дополнительные данные в аудит."""
    if hasattr(request.state, 'audit_context'):
        ctx = request.state.audit_context
        if ctx.extra_data is None:
            ctx.extra_data = {}
        ctx.extra_data[key] = value
