"""Session schemas for user session management."""

from datetime import datetime

from pydantic import BaseModel, Field


class DeviceInfo(BaseModel):
    """Parsed device information from fingerprint."""

    platform: str | None = None
    browser: str | None = None
    screen: str | None = None


class SessionResponse(BaseModel):
    """Single session info."""

    session_id: str
    created_at: datetime
    ip_address: str | None = Field(None, description="Masked IP (e.g., 192.168.x.x)")
    device: DeviceInfo
    is_current: bool = False


class SessionListResponse(BaseModel):
    """List of user sessions."""

    sessions: list[SessionResponse]
    total: int
    max_sessions: int


class RevokeSessionsResponse(BaseModel):
    """Response after revoking sessions."""

    revoked_count: int
    message: str
