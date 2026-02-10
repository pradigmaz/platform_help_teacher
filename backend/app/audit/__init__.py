"""
Student Audit System - полный сбор данных о действиях.
Тихий режим: студенты не знают о логировании.
"""

from .bot_audit import (
    log_bot_action,
    log_bot_auth,
    log_bot_bind,
    log_bot_message,
    log_bot_start,
)
from .constants import ActionType, EntityType
from .decorators import audit_action
from .middleware import AuditMiddleware
from .service import AuditService, get_audit_service

__all__ = [
    "ActionType",
    "EntityType",
    "AuditService",
    "get_audit_service",
    "AuditMiddleware",
    "audit_action",
    # Bot audit
    "log_bot_action",
    "log_bot_start",
    "log_bot_auth",
    "log_bot_bind",
    "log_bot_message",
]
