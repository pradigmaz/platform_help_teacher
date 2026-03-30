"""
Result models and status constants for backup flows.
"""

from dataclasses import dataclass

from .encryption import BackupFileInfo

VERIFY_STATUS_VALID = "valid"
VERIFY_STATUS_DOWNLOAD_FAILED = "download_failed"
VERIFY_STATUS_FILE_CORRUPTED = "file_corrupted"
VERIFY_STATUS_RECOVERY_CODE_REQUIRED = "recovery_code_required"
VERIFY_STATUS_INVALID_RECOVERY_CODE = "invalid_recovery_code"
VERIFY_STATUS_DECRYPTION_FAILED = "decryption_failed"
VERIFY_STATUS_ARCHIVE_CORRUPTED = "archive_corrupted"
VERIFY_STATUS_DUMP_INVALID = "dump_invalid"


@dataclass
class BackupResult:
    success: bool
    backup_key: str | None = None
    recovery_code: str | None = None
    format_version: int | None = None
    portable: bool | None = None
    key_fingerprint: str | None = None
    created_with_current_key: bool | None = None
    size: int | None = None
    uploaded: bool = False
    mirrored_offsite: bool | None = None
    offsite_error: str | None = None
    notification_sent: bool | None = None
    notification_error: str | None = None
    error: str | None = None


@dataclass
class RestoreResult:
    success: bool
    error: str | None = None
    status: str | None = None
    format_version: int | None = None
    portable: bool | None = None
    created_with_current_key: bool | None = None
    offsite_used: bool | None = None


@dataclass
class VerifyResult:
    valid: bool
    status: str
    error: str | None = None
    format_version: int | None = None
    portable: bool | None = None
    created_with_current_key: bool | None = None
    offsite_used: bool | None = None


def build_backup_success_result(
    *,
    remote_key: str,
    recovery_code: str,
    format_version: int,
    key_fingerprint: str,
    size: int,
    mirrored_offsite: bool | None,
    offsite_error: str | None,
    notification_sent: bool | None,
    notification_error: str | None,
) -> BackupResult:
    return BackupResult(
        success=True,
        backup_key=remote_key,
        recovery_code=recovery_code,
        format_version=format_version,
        portable=True,
        key_fingerprint=key_fingerprint,
        created_with_current_key=True,
        size=size,
        uploaded=True,
        mirrored_offsite=mirrored_offsite,
        offsite_error=offsite_error,
        notification_sent=notification_sent,
        notification_error=notification_error,
    )


def build_restore_result(
    *,
    success: bool,
    status: str,
    current_key_fingerprint: str,
    error: str | None = None,
    file_info: BackupFileInfo | None = None,
    offsite_used: bool | None = None,
) -> RestoreResult:
    return RestoreResult(
        success=success,
        status=status,
        error=error,
        format_version=file_info.format_version if file_info else None,
        portable=file_info.portable if file_info else None,
        created_with_current_key=_created_with_current_key(file_info, current_key_fingerprint),
        offsite_used=offsite_used,
    )


def build_verify_result(
    *,
    valid: bool,
    status: str,
    current_key_fingerprint: str,
    error: str | None = None,
    file_info: BackupFileInfo | None = None,
    offsite_used: bool | None = None,
) -> VerifyResult:
    return VerifyResult(
        valid=valid,
        status=status,
        error=error,
        format_version=file_info.format_version if file_info else None,
        portable=file_info.portable if file_info else None,
        created_with_current_key=_created_with_current_key(file_info, current_key_fingerprint),
        offsite_used=offsite_used,
    )


def _created_with_current_key(file_info: BackupFileInfo | None, current_key_fingerprint: str) -> bool | None:
    if not file_info or not file_info.key_fingerprint:
        return None
    return file_info.key_fingerprint == current_key_fingerprint
