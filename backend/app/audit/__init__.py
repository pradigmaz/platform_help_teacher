"""
Student Audit System - полный сбор данных о действиях.
Тихий режим: студенты не знают о логировании.
"""
from .constants import ActionType, EntityType
from .service import AuditService, get_audit_service
from .middleware import AuditMiddleware
from .decorators import audit_action
from .deps import audit_user, get_audit_context
from .bot_audit import (
    log_bot_action,
    log_bot_start,
    log_bot_auth,
    log_bot_bind,
    log_bot_message,
)

__all__ = [
    "ActionType",
    "EntityType", 
    "AuditService",
    "get_audit_service",
    "AuditMiddleware",
    "audit_action",
    "audit_user",
    "get_audit_context",
    # Bot audit
    "log_bot_action",
    "log_bot_start",
    "log_bot_auth",
    "log_bot_bind",
    "log_bot_message",
]
