"""
Helpers for backup artifact naming and metadata.
"""

import logging
import secrets
from datetime import datetime
from pathlib import Path

from .encryption import BackupEncryption

logger = logging.getLogger(__name__)


def secure_delete(file_path: Path) -> None:
    """
    Overwrite a file with random data before unlinking it.
    """
    if not file_path.exists():
        return

    try:
        size = file_path.stat().st_size
        with open(file_path, "wb") as file_handle:
            remaining = size
            chunk_size = 64 * 1024
            while remaining > 0:
                write_size = min(chunk_size, remaining)
                file_handle.write(secrets.token_bytes(write_size))
                remaining -= write_size
            file_handle.flush()
        file_path.unlink()
    except Exception as exc:
        logger.warning("Secure delete failed, falling back to unlink: %s", exc)
        if file_path.exists():
            file_path.unlink()


def generate_backup_name(prefix: str = "backup") -> str:
    """
    Generate a human-readable backup name with randomized entropy.
    """
    return f"{prefix}_{datetime.now().strftime('%Y%m%d')}_{secrets.token_hex(4)}"


def build_backup_object_metadata(
    encryption: BackupEncryption,
    *,
    format_version: int,
    portable: bool,
) -> dict[str, str]:
    return {
        "backup-format-version": str(format_version),
        "backup-portable": str(portable).lower(),
        "backup-key-fingerprint": encryption.key_fingerprint,
    }
