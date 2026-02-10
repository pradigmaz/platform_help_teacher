"""
Pydantic схемы для аудита.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class AuditContext(BaseModel):
    """Контекст аудита, собираемый во время запроса."""

    request_id: str
    correlation_id: str | None = None  # Для связи цепочки действий

    # User
    user_id: UUID | None = None
    session_id: str | None = None
    actor_role: str = "anonymous"  # student/teacher/admin/anonymous

    # Action
    action_type: str = "view"
    entity_type: str | None = None
    entity_id: UUID | None = None

    # HTTP
    method: str
    path: str
    query_params: dict[str, Any] | None = None
    request_body: dict[str, Any] | None = None
    response_status: int | None = None
    duration_ms: int | None = None

    # Client
    ip_address: str
    ip_forwarded: str | None = None
    user_agent: str | None = None

    # Extra
    fingerprint: dict[str, Any] | None = None
    extra_data: dict[str, Any] | None = None

    class Config:
        from_attributes = True


class AuditLogCreate(BaseModel):
    """Схема для создания записи аудита."""

    user_id: UUID | None = None
    session_id: str | None = None
    correlation_id: str | None = None
    actor_role: str = "anonymous"
    action_type: str
    entity_type: str | None = None
    entity_id: UUID | None = None
    method: str
    path: str
    query_params: dict[str, Any] | None = None
    request_body: dict[str, Any] | None = None
    response_status: int | None = None
    duration_ms: int | None = None
    ip_address: str
    ip_forwarded: str | None = None
    user_agent: str | None = None
    fingerprint: dict[str, Any] | None = None
    extra_data: dict[str, Any] | None = None


class IPInfo(BaseModel):
    """Информация об IP адресе."""

    real_ip: str
    forwarded_chain: str | None = None
    is_proxy: bool = False


# Response schemas for API
class AuditLogResponse(BaseModel):
    """Ответ с записью аудита."""

    id: UUID
    user_id: UUID | None = None
    user_name: str | None = None
    actor_role: str = "anonymous"
    action_type: str
    entity_type: str | None = None
    entity_id: UUID | None = None
    method: str
    path: str
    query_params: dict[str, Any] | None = None
    request_body: dict[str, Any] | None = None
    response_status: int | None = None
    duration_ms: int | None = None
    ip_address: str
    ip_forwarded: str | None = None
    user_agent: str | None = None
    fingerprint: dict[str, Any] | None = None
    extra_data: dict[str, Any] | None = None
    created_at: datetime
    suspicion: dict[str, Any] | None = None  # Подозрение на анонимный запрос

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Список записей аудита с пагинацией."""

    items: list[AuditLogResponse]
    total: int
    skip: int
    limit: int


class AuditStatsResponse(BaseModel):
    """Статистика аудита."""

    total_logs: int
    unique_users: int
    unique_ips: int
    by_action_type: dict[str, int]
    period_days: int
