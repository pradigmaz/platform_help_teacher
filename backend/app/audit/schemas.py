"""
Pydantic схемы для аудита.
"""
from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AuditContext(BaseModel):
    """Контекст аудита, собираемый во время запроса."""
    request_id: str
    
    # User
    user_id: Optional[UUID] = None
    session_id: Optional[str] = None
    
    # Action
    action_type: str = "view"
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    
    # HTTP
    method: str
    path: str
    query_params: Optional[Dict[str, Any]] = None
    request_body: Optional[Dict[str, Any]] = None
    response_status: Optional[int] = None
    duration_ms: Optional[int] = None
    
    # Client
    ip_address: str
    ip_forwarded: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Extra
    fingerprint: Optional[Dict[str, Any]] = None
    extra_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class AuditLogCreate(BaseModel):
    """Схема для создания записи аудита."""
    user_id: Optional[UUID] = None
    session_id: Optional[str] = None
    action_type: str
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    method: str
    path: str
    query_params: Optional[Dict[str, Any]] = None
    request_body: Optional[Dict[str, Any]] = None
    response_status: Optional[int] = None
    duration_ms: Optional[int] = None
    ip_address: str
    ip_forwarded: Optional[str] = None
    user_agent: Optional[str] = None
    fingerprint: Optional[Dict[str, Any]] = None
    extra_data: Optional[Dict[str, Any]] = None


class IPInfo(BaseModel):
    """Информация об IP адресе."""
    real_ip: str
    forwarded_chain: Optional[str] = None
    is_proxy: bool = False



# Response schemas for API
class AuditLogResponse(BaseModel):
    """Ответ с записью аудита."""
    id: UUID
    user_id: Optional[UUID] = None
    user_name: Optional[str] = None
    action_type: str
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    method: str
    path: str
    query_params: Optional[Dict[str, Any]] = None
    request_body: Optional[Dict[str, Any]] = None
    response_status: Optional[int] = None
    duration_ms: Optional[int] = None
    ip_address: str
    ip_forwarded: Optional[str] = None
    user_agent: Optional[str] = None
    fingerprint: Optional[Dict[str, Any]] = None
    extra_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    suspicion: Optional[Dict[str, Any]] = None  # Подозрение на анонимный запрос

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
    by_action_type: Dict[str, int]
    period_days: int
