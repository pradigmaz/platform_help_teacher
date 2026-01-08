"""
Pydantic schemas for backup API.
"""
import re
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# Security: Only allow safe backup key format
SAFE_BACKUP_KEY_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,100}\.enc$')


def validate_backup_key(key: str) -> str:
    """
    Validate backup key to prevent path traversal attacks.
    Only allows: alphanumeric, underscore, hyphen, ending with .enc
    """
    if not SAFE_BACKUP_KEY_PATTERN.match(key):
        raise ValueError(
            "Invalid backup key format. "
            "Must be alphanumeric with underscores/hyphens, ending with .enc"
        )
    # Extra safety: reject any path separators
    if '/' in key or '\\' in key or '..' in key:
        raise ValueError("Path separators not allowed in backup key")
    return key


class BackupCreate(BaseModel):
    """Request to create a backup."""
    name: Optional[str] = Field(None, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')


class BackupInfo(BaseModel):
    """Backup metadata response."""
    name: str
    key: str
    size: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class BackupListResponse(BaseModel):
    """List of backups response."""
    backups: List[BackupInfo]
    total: int


class BackupCreateResponse(BaseModel):
    """Response after creating backup."""
    success: bool
    backup_key: Optional[str] = None
    size: Optional[int] = None
    error: Optional[str] = None


class RestoreRequest(BaseModel):
    """Request to restore a backup."""
    drop_existing: bool = Field(False, description="Drop existing objects before restore")
    confirmation: str = Field(
        ..., 
        min_length=10,
        description="Type 'RESTORE-{backup_key}' to confirm destructive operation"
    )


class RestoreResponse(BaseModel):
    """Response after restore operation."""
    success: bool
    error: Optional[str] = None


class VerifyResponse(BaseModel):
    """Response after backup verification."""
    valid: bool
    backup_key: str


class BackupSettingsSchema(BaseModel):
    """Backup settings response/update."""
    enabled: bool = True
    schedule_hour: int = Field(17, ge=0, le=23)
    schedule_minute: int = Field(0, ge=0, le=59)
    retention_days: int = Field(30, ge=1, le=365)
    max_backups: int = Field(10, ge=1, le=100)
    storage_bucket: str = "edu-backups"
    notify_on_success: bool = False
    notify_on_failure: bool = True
    
    class Config:
        from_attributes = True


class BackupSettingsUpdate(BaseModel):
    """Partial update for backup settings."""
    enabled: Optional[bool] = None
    schedule_hour: Optional[int] = Field(None, ge=0, le=23)
    schedule_minute: Optional[int] = Field(None, ge=0, le=59)
    retention_days: Optional[int] = Field(None, ge=1, le=365)
    max_backups: Optional[int] = Field(None, ge=1, le=100)
    notify_on_success: Optional[bool] = None
    notify_on_failure: Optional[bool] = None
