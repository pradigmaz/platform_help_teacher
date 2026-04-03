"""
Helpers for backup upload and offsite mirroring.
"""

import asyncio
import logging
from pathlib import Path
from typing import cast

from .remote_storage import BackupStorage
from .storage_utils import BackupMetadata

logger = logging.getLogger(__name__)


async def annotate_offsite_presence(
    backups: list[BackupMetadata],
    offsite_storage: BackupStorage | None,
) -> list[BackupMetadata]:
    if not backups or not offsite_storage:
        return backups

    statuses = await asyncio.gather(
        *(offsite_storage.exists(backup.key) for backup in backups),
        return_exceptions=True,
    )
    for backup, status in zip(backups, statuses, strict=False):
        backup.offsite_present = False if isinstance(status, BaseException) else cast(bool, status)
    return backups


async def mirror_backup_upload(
    file_path: Path,
    remote_key: str,
    object_metadata: dict[str, str],
    offsite_storage: BackupStorage | None,
) -> tuple[bool | None, str | None]:
    if not offsite_storage:
        return None, None

    try:
        await offsite_storage.upload(file_path, remote_key, object_metadata=object_metadata)
        return True, None
    except Exception as exc:
        error = str(exc).strip() or "Offsite mirror failed"
        logger.error("Offsite mirror failed for %s: %s", remote_key, error)
        return False, error


def mirror_backup_upload_sync(
    file_path: Path,
    remote_key: str,
    object_metadata: dict[str, str],
    offsite_storage: BackupStorage | None,
) -> tuple[bool | None, str | None]:
    if not offsite_storage:
        return None, None

    try:
        offsite_storage.upload_sync(file_path, remote_key, verify=True, object_metadata=object_metadata)
        return True, None
    except Exception as exc:
        error = str(exc).strip() or "Offsite mirror failed"
        logger.error("Offsite mirror failed for %s: %s", remote_key, error)
        return False, error
