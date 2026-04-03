"""
Pydantic schemas for backup API.
"""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# Security: Only allow safe backup key format
SAFE_BACKUP_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,100}\.enc$")

# Max upload size: 50MB (Telegram limit, VK allows 200MB)
MAX_BACKUP_UPLOAD_SIZE = 50 * 1024 * 1024


def validate_backup_key(key: str) -> str:
    """
    Validate backup key to prevent path traversal attacks.
    Only allows: alphanumeric, underscore, hyphen, ending with .enc
    """
    if not SAFE_BACKUP_KEY_PATTERN.match(key):
        raise ValueError("Invalid backup key format. Must be alphanumeric with underscores/hyphens, ending with .enc")
    if "/" in key or "\\" in key or ".." in key:
        raise ValueError("Path separators not allowed in backup key")
    return key


class BackupCreate(BaseModel):
    """Request to create a backup."""

    name: str | None = Field(None, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")


class BackupInfo(BaseModel):
    """Backup metadata response."""

    name: str
    key: str
    size: int
    created_at: datetime
    format_version: int | None = None
    portable: bool | None = None
    key_fingerprint: str | None = None
    created_with_current_key: bool | None = None
    offsite_present: bool | None = None

    model_config = ConfigDict(from_attributes=True)


class BackupListResponse(BaseModel):
    """List of backups response."""

    backups: list[BackupInfo]
    total: int


class BackupCreateResponse(BaseModel):
    """Response after creating backup."""

    success: bool
    backup_key: str | None = None
    recovery_code: str | None = None
    portable: bool = False
    format_version: int | None = None
    key_fingerprint: str | None = None
    created_with_current_key: bool | None = None
    size: int | None = None
    uploaded: bool = False
    mirrored_offsite: bool | None = None
    offsite_error: str | None = None
    notification_sent: bool | None = None
    notification_error: str | None = None
    error: str | None = None


class RestoreRequest(BaseModel):
    """Request to restore a backup."""

    drop_existing: bool = Field(False, description="Drop existing objects before restore")
    recovery_code: str | None = Field(None, min_length=16, description="Portable backup recovery code")
    confirmation: str = Field(
        ..., min_length=10, description="Type 'RESTORE-{backup_key}' to confirm destructive operation"
    )


class RestoreResponse(BaseModel):
    """Response after restore operation."""

    success: bool
    status: str | None = None
    error: str | None = None
    format_version: int | None = None
    portable: bool | None = None
    created_with_current_key: bool | None = None
    offsite_used: bool | None = None


class VerifyRequest(BaseModel):
    """Optional verification parameters."""

    recovery_code: str | None = Field(None, min_length=16, description="Portable backup recovery code")


class VerifyResponse(BaseModel):
    """Response after backup verification."""

    valid: bool
    backup_key: str
    status: str
    error: str | None = None
    format_version: int | None = None
    portable: bool | None = None
    created_with_current_key: bool | None = None
    offsite_used: bool | None = None


class BackupSettingsSchema(BaseModel):
    """Backup settings response/update."""

    enabled: bool = True
    schedule_hour: int = Field(17, ge=0, le=23)
    schedule_minute: int = Field(0, ge=0, le=59)
    retention_days: int = Field(30, ge=1, le=365)
    max_backups: int = Field(10, ge=1, le=100)
    notify_on_success: bool = False
    notify_on_failure: bool = True

    model_config = ConfigDict(from_attributes=True)


class BackupSettingsUpdate(BaseModel):
    """Partial update for backup settings."""

    enabled: bool | None = None
    schedule_hour: int | None = Field(None, ge=0, le=23)
    schedule_minute: int | None = Field(None, ge=0, le=59)
    retention_days: int | None = Field(None, ge=1, le=365)
    max_backups: int | None = Field(None, ge=1, le=100)
    notify_on_success: bool | None = None
    notify_on_failure: bool | None = None


class UploadBackupResponse(BaseModel):
    """Response after uploading backup file."""

    success: bool
    backup_key: str | None = None
    size: int | None = None
    verified: bool | None = None
    verification_status: str | None = None
    format_version: int | None = None
    portable: bool | None = None
    created_with_current_key: bool | None = None
    mirrored_offsite: bool | None = None
    offsite_error: str | None = None
    error: str | None = None


class BotStatusResponse(BaseModel):
    """Status of available notification bots."""

    telegram_available: bool
    vk_available: bool
    telegram_admin_id: int | None = None
    vk_admin_id: int | None = None


class BackupHealthCheck(BaseModel):
    status: str
    message: str | None = None
    count: int | None = None
    latest: str | None = None
    path: str | None = None
    configured: bool | None = None
    latest_backup_mirrored: bool | None = None


class BackupFreshness(BaseModel):
    status: str | None = None
    latest_backup_key: str | None = None
    latest_backup_at: datetime | None = None
    age_hours: float | None = None
    expected_max_age_hours: float | None = None
    message: str | None = None


class BackupOffsiteStatus(BaseModel):
    configured: bool
    status: str | None = None
    latest_backup_mirrored: bool | None = None
    message: str | None = None


class BackupHealthResponse(BaseModel):
    status: str
    checks: dict[str, BackupHealthCheck]
    freshness: BackupFreshness | None = None
    offsite: BackupOffsiteStatus | None = None
