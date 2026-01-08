"""
Декораторы для добавления семантики в аудит.
"""
import functools
import logging
from typing import Callable, Optional, Any
from uuid import UUID

from fastapi import Request

from .constants import ActionType, EntityType

logger = logging.getLogger(__name__)


def audit_action(
    action_type: ActionType,
    entity_type: Optional[EntityType] = None,
    entity_id_param: Optional[str] = None,
):
    """
    Декоратор для добавления семантики действия в аудит.
    
    Args:
        action_type: Тип действия (SUBMIT, CANCEL, VIEW, etc.)
        entity_type: Тип сущности (lab, submission, etc.)
        entity_id_param: Имя параметра с ID сущности (lab_id, etc.)
    
    Usage:
        @router.post("/labs/{lab_id}/ready")
        @audit_action(ActionType.SUBMIT, EntityType.SUBMISSION, "lab_id")
        async def mark_lab_ready(lab_id: UUID, request: Request, ...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Ищем Request в аргументах
            request = _find_request(args, kwargs)
            
            if request and hasattr(request.state, 'audit_context'):
                ctx = request.state.audit_context
                ctx.action_type = action_type.value
                
                if entity_type:
                    ctx.entity_type = entity_type.value
                
                # Извлекаем entity_id из параметров
                if entity_id_param and entity_id_param in kwargs:
                    entity_id = kwargs[entity_id_param]
                    if isinstance(entity_id, UUID):
                        ctx.entity_id = entity_id
                    elif isinstance(entity_id, str):
                        try:
                            ctx.entity_id = UUID(entity_id)
                        except ValueError:
                            pass
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def _find_request(args: tuple, kwargs: dict) -> Optional[Request]:
    """Найти объект Request в аргументах функции."""
    # Проверяем kwargs
    if 'request' in kwargs:
        return kwargs['request']
    
    # Проверяем args
    for arg in args:
        if isinstance(arg, Request):
            return arg
    
    return None
