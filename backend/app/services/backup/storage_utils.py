"""
Shared helpers for backup storage metadata and verification.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.core.config import settings

BACKUP_METADATA_FORMAT_VERSION = "backup-format-version"
BACKUP_METADATA_PORTABLE = "backup-portable"
BACKUP_METADATA_KEY_FINGERPRINT = "backup-key-fingerprint"


def compute_md5(file_path: Path) -> str:
    md5 = hashlib.md5()
    with open(file_path, "rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(64 * 1024), b""):
            md5.update(chunk)
    return md5.hexdigest()


def upload_verification_error(response: dict, local_path: Path, local_md5: str) -> str | None:
    remote_etag = response.get("ETag", "").strip('"')
    remote_size = response.get("ContentLength", 0)
    local_size = local_path.stat().st_size
    if "-" in remote_etag:
        if remote_size != local_size:
            return f"Upload size mismatch: local={local_size}, remote={remote_size}"
        return None
    if remote_etag != local_md5:
        return f"Upload verification failed: local={local_md5}, remote={remote_etag}"
    return None


def normalize_endpoint(endpoint: str, default_scheme: str = "http") -> str:
    endpoint = endpoint.strip()
    if endpoint.startswith(("http://", "https://")):
        return endpoint
    return f"{default_scheme}://{endpoint}"


def normalize_object_metadata(metadata: dict[str, str] | None) -> dict[str, str]:
    if not metadata:
        return {}
    return {str(key).lower(): str(value) for key, value in metadata.items() if value is not None}


def _parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False
    return None


def _current_key_fingerprint() -> str | None:
    if not settings.BACKUP_ENCRYPTION_KEY or len(settings.BACKUP_ENCRYPTION_KEY) < 32:
        return None
    return hashlib.sha256(settings.BACKUP_ENCRYPTION_KEY.encode()).digest()[:8].hex()


@dataclass(frozen=True)
class BackupObjectMetadata:
    format_version: int | None = None
    portable: bool | None = None
    key_fingerprint: str | None = None
    created_with_current_key: bool | None = None


@dataclass
class BackupMetadata:
    name: str
    size: int
    created_at: datetime
    key: str
    etag: str | None = None
    format_version: int | None = None
    portable: bool | None = None
    key_fingerprint: str | None = None
    created_with_current_key: bool | None = None
    offsite_present: bool | None = None


def parse_backup_object_metadata(raw_metadata: dict[str, str] | None) -> BackupObjectMetadata:
    metadata = normalize_object_metadata(raw_metadata)
    format_version = metadata.get(BACKUP_METADATA_FORMAT_VERSION)
    key_fingerprint = metadata.get(BACKUP_METADATA_KEY_FINGERPRINT)
    current_key_fingerprint = _current_key_fingerprint()
    return BackupObjectMetadata(
        format_version=int(format_version) if format_version and format_version.isdigit() else None,
        portable=_parse_bool(metadata.get(BACKUP_METADATA_PORTABLE)),
        key_fingerprint=key_fingerprint,
        created_with_current_key=(
            key_fingerprint == current_key_fingerprint if key_fingerprint and current_key_fingerprint else None
        ),
    )


def build_backup_metadata(
    remote_key: str,
    *,
    size: int,
    created_at: datetime,
    etag: str | None = None,
    raw_metadata: dict[str, str] | None = None,
) -> BackupMetadata:
    parsed = parse_backup_object_metadata(raw_metadata)
    return BackupMetadata(
        name=Path(remote_key).stem,
        size=size,
        created_at=created_at,
        key=remote_key,
        etag=etag,
        format_version=parsed.format_version,
        portable=parsed.portable,
        key_fingerprint=parsed.key_fingerprint,
        created_with_current_key=parsed.created_with_current_key,
    )
