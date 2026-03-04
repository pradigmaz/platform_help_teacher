"""Device schemas for API validation."""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DeviceBase(BaseModel):
    """Base device schema."""
    fingerprint_hash: str = Field(
        ..., min_length=64, max_length=64,
        description="SHA256 hash of device fingerprint",
    )
    device_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Device information (platform, browser, etc.)",
    )


class DeviceCreate(DeviceBase):
    """Schema for creating a device."""
    pass


class DeviceUpdate(BaseModel):
    """Schema for updating a device."""
    device_info: Optional[Dict[str, Any]] = None
    last_seen: Optional[datetime] = None
    is_trusted: Optional[bool] = None
    confirmed_at: Optional[datetime] = None


class DeviceResponse(DeviceBase):
    """Full device response (internal/admin use)."""
    id: UUID
    user_id: UUID
    first_seen: datetime
    last_seen: datetime
    is_trusted: bool
    confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DevicePublicResponse(BaseModel):
    """Public device response — without fingerprint_hash."""
    id: UUID
    user_id: UUID
    device_info: Dict[str, Any] = Field(default_factory=dict)
    first_seen: datetime
    last_seen: datetime
    is_trusted: bool
    confirmed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    """Paginated device list response."""
    devices: list[DevicePublicResponse]
    total: int
