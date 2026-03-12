"""
Backup creation service.
Handles pg_dump, compression, encryption, and upload.
"""

import asyncio
import gzip
import logging
import secrets
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.core.time_constants import BACKUP_DUMP_TIMEOUT_SECONDS

from .encryption import BackupEncryption
from .notification import get_notification_service
from .remote_storage import BackupMetadata, BackupStorage, get_offsite_storage

logger = logging.getLogger(__name__)


def _secure_delete(file_path: Path) -> None:
    """
    Securely delete a file by overwriting with random data before unlinking.
    Prevents data recovery from disk.
    """
    if not file_path.exists():
        return

    try:
        size = file_path.stat().st_size
        # Overwrite with random data
        with open(file_path, "wb") as f:
            # Write in chunks to handle large files
            chunk_size = 64 * 1024
            remaining = size
            while remaining > 0:
                write_size = min(chunk_size, remaining)
                f.write(secrets.token_bytes(write_size))
                remaining -= write_size
            f.flush()
        # Then unlink
        file_path.unlink()
    except Exception as e:
        # Fallback to regular delete
        logger.warning(f"Secure delete failed, using regular delete: {e}")
        if file_path.exists():
            file_path.unlink()


def _generate_backup_name(prefix: str = "backup") -> str:
    """
    Generate backup name with UUID instead of timestamp.
    Prevents timing analysis attacks.
    """
    # 8 random hex chars = 32 bits of entropy
    random_id = secrets.token_hex(4)
    # Include date (not time) for human readability
    date_str = datetime.now().strftime("%Y%m%d")
    return f"{prefix}_{date_str}_{random_id}"


@dataclass
class BackupResult:
    """Result of backup operation."""

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


def _build_backup_object_metadata(
    encryption: BackupEncryption, *, format_version: int, portable: bool
) -> dict[str, str]:
    return {
        "backup-format-version": str(format_version),
        "backup-portable": str(portable).lower(),
        "backup-key-fingerprint": encryption.key_fingerprint,
    }


class BackupService:
    """Service for creating encrypted PostgreSQL backups."""

    def __init__(self):
        self.encryption = BackupEncryption(settings.BACKUP_ENCRYPTION_KEY)
        self.storage = BackupStorage()
        self.offsite_storage = get_offsite_storage()

    async def _annotate_offsite_presence(self, backups: list[BackupMetadata]) -> list[BackupMetadata]:
        if not backups or not self.offsite_storage:
            return backups

        statuses = await asyncio.gather(
            *(self.offsite_storage.exists(backup.key) for backup in backups),
            return_exceptions=True,
        )
        for backup, status in zip(backups, statuses, strict=False):
            backup.offsite_present = False if isinstance(status, Exception) else status
        return backups

    async def create_backup(
        self,
        name: str | None = None,
        send_to_admin: bool = True,
        notify_on_failure: bool = True,
    ) -> BackupResult:
        """
        Create encrypted backup of PostgreSQL database.

        Steps:
        1. pg_dump --format=custom
        2. gzip compression
        3. AES-256-GCM encryption
        4. Upload to remote storage
        5. Send to admin via Telegram (optional)
        6. Cleanup temp files
        """
        backup_name = name or _generate_backup_name()
        remote_key = f"{backup_name}.enc"

        if await self.storage.exists(remote_key):
            return BackupResult(success=False, backup_key=remote_key, error="Backup with this name already exists")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            dump_file = tmp_path / f"{backup_name}.dump"
            compressed_file = tmp_path / f"{backup_name}.dump.gz"
            encrypted_file = tmp_path / f"{backup_name}.enc"

            try:
                # Step 1: pg_dump
                logger.info(f"Starting backup: {backup_name}")
                await self._pg_dump(dump_file)

                # Step 2: Compress
                self._compress(dump_file, compressed_file)
                _secure_delete(dump_file)  # Secure cleanup uncompressed

                # Step 3: Encrypt
                recovery_code = self.encryption.encrypt_file(compressed_file, encrypted_file)
                _secure_delete(compressed_file)  # Secure cleanup compressed
                format_version = self.encryption.current_format_version
                portable = True
                object_metadata = _build_backup_object_metadata(
                    self.encryption,
                    format_version=format_version,
                    portable=portable,
                )

                # Step 4: Upload
                await self.storage.upload(encrypted_file, remote_key, object_metadata=object_metadata)
                mirrored_offsite = None
                offsite_error = None
                if self.offsite_storage:
                    try:
                        await self.offsite_storage.upload(encrypted_file, remote_key, object_metadata=object_metadata)
                        mirrored_offsite = True
                    except Exception as exc:
                        mirrored_offsite = False
                        offsite_error = str(exc).strip() or "Offsite mirror failed"
                        logger.error("Offsite mirror failed for %s: %s", remote_key, offsite_error)

                size = encrypted_file.stat().st_size
                logger.info(f"Backup completed: {remote_key} ({size} bytes)")

                # Step 5: Send to admin via Telegram
                notification_sent = None
                notification_error = None
                if send_to_admin:
                    notifier = get_notification_service()
                    notification_result = await notifier.send_backup_to_admin(
                        file_path=encrypted_file,
                        backup_name=remote_key,
                        size=size,
                    )
                    notification_sent = notification_result.success
                    notification_error = notification_result.error
                    if not notification_result.success and notification_result.error:
                        logger.warning(notification_result.error)

                return BackupResult(
                    success=True,
                    backup_key=remote_key,
                    recovery_code=recovery_code,
                    format_version=format_version,
                    portable=portable,
                    key_fingerprint=self.encryption.key_fingerprint,
                    created_with_current_key=True,
                    size=size,
                    uploaded=True,
                    mirrored_offsite=mirrored_offsite,
                    offsite_error=offsite_error,
                    notification_sent=notification_sent,
                    notification_error=notification_error,
                )

            except Exception as e:
                import traceback

                tb_text = traceback.format_exc()
                logger.error(f"Backup failed: {e}\n{tb_text}")
                # Notify admin about failure with full traceback
                if notify_on_failure:
                    notifier = get_notification_service()
                    notify_result = await notifier.notify_backup_failure(str(e), traceback_text=tb_text)
                    if not notify_result.success and notify_result.error:
                        logger.warning(notify_result.error)
                return BackupResult(success=False, error=str(e))

    async def _pg_dump(self, output_path: Path) -> None:
        """Execute pg_dump command using .pgpass file for security."""
        import os

        # Create temporary .pgpass file (more secure than PGPASSWORD env)
        pgpass_path = output_path.parent / ".pgpass"
        pgpass_content = (
            f"{settings.POSTGRES_SERVER}:"
            f"{settings.POSTGRES_PORT}:"
            f"{settings.POSTGRES_DB}:"
            f"{settings.POSTGRES_USER}:"
            f"{settings.POSTGRES_PASSWORD}"
        )

        try:
            # Write .pgpass with restricted permissions
            pgpass_path.write_text(pgpass_content)
            os.chmod(pgpass_path, 0o600)  # Required by PostgreSQL

            cmd = [
                "pg_dump",
                "--format=custom",
                "--no-password",
                f"--host={settings.POSTGRES_SERVER}",
                f"--port={settings.POSTGRES_PORT}",
                f"--username={settings.POSTGRES_USER}",
                f"--dbname={settings.POSTGRES_DB}",
                f"--file={output_path}",
            ]

            # Use PGPASSFILE instead of PGPASSWORD (not visible in /proc)
            env = {**dict(os.environ), "PGPASSFILE": str(pgpass_path)}

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                _, stderr = await asyncio.wait_for(proc.communicate(), timeout=BACKUP_DUMP_TIMEOUT_SECONDS)
            except TimeoutError as exc:
                proc.kill()
                await proc.wait()
                raise RuntimeError(f"pg_dump timed out after {BACKUP_DUMP_TIMEOUT_SECONDS} seconds") from exc

            if proc.returncode != 0:
                raise RuntimeError(f"pg_dump failed: {stderr.decode()}")

            logger.info(f"pg_dump completed: {output_path.stat().st_size} bytes")

        finally:
            # Always cleanup .pgpass
            if pgpass_path.exists():
                pgpass_path.unlink()

    def _compress(self, input_path: Path, output_path: Path) -> None:
        """Compress file using gzip."""
        with open(input_path, "rb") as f_in, gzip.open(output_path, "wb", compresslevel=6) as f_out:
            while chunk := f_in.read(64 * 1024):
                f_out.write(chunk)

        logger.info(f"Compressed: {input_path.stat().st_size} -> {output_path.stat().st_size}")

    async def list_backups(self) -> list[BackupMetadata]:
        """List all available backups."""
        backups = await self.storage.list_backups()
        return await self._annotate_offsite_presence(backups)

    async def delete_backup(self, backup_key: str) -> bool:
        """Delete a backup by key."""
        try:
            await self.storage.delete(backup_key)
            if self.offsite_storage:
                try:
                    await self.offsite_storage.delete(backup_key)
                except Exception as exc:
                    logger.warning("Failed to delete offsite backup %s: %s", backup_key, exc)
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False

    async def cleanup_old_backups(self, retention_days: int = None) -> int:
        """Delete backups older than retention period."""
        from app.core.time_constants import BACKUP_RETENTION_DAYS

        retention = retention_days or BACKUP_RETENTION_DAYS
        cutoff = datetime.now().timestamp() - (retention * 86400)

        backups = await self.list_backups()
        deleted = 0

        for backup in backups:
            if backup.created_at.timestamp() < cutoff:
                await self.delete_backup(backup.key)
                deleted += 1
                logger.info(f"Deleted old backup: {backup.key}")

        return deleted

    # ========== SYNC METHODS FOR CELERY ==========

    def create_backup_sync(
        self,
        name: str | None = None,
        send_to_admin: bool = True,
        notify_on_failure: bool = True,
    ) -> BackupResult:
        """
        Синхронная версия create_backup для Celery tasks.
        Использует subprocess вместо asyncio для pg_dump.
        """

        backup_name = name or _generate_backup_name()
        remote_key = f"{backup_name}.enc"

        if self.storage.exists_sync(remote_key):
            return BackupResult(success=False, backup_key=remote_key, error="Backup with this name already exists")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            dump_file = tmp_path / f"{backup_name}.dump"
            compressed_file = tmp_path / f"{backup_name}.dump.gz"
            encrypted_file = tmp_path / f"{backup_name}.enc"

            try:
                # Step 1: pg_dump (sync)
                logger.info(f"Starting backup: {backup_name}")
                self._pg_dump_sync(dump_file)

                # Step 2: Compress
                self._compress(dump_file, compressed_file)
                _secure_delete(dump_file)

                # Step 3: Encrypt
                recovery_code = self.encryption.encrypt_file(compressed_file, encrypted_file)
                _secure_delete(compressed_file)
                format_version = self.encryption.current_format_version
                portable = True
                object_metadata = _build_backup_object_metadata(
                    self.encryption,
                    format_version=format_version,
                    portable=portable,
                )

                # Step 4: Upload (sync)
                self.storage.upload_sync(encrypted_file, remote_key, verify=True, object_metadata=object_metadata)
                mirrored_offsite = None
                offsite_error = None
                if self.offsite_storage:
                    try:
                        self.offsite_storage.upload_sync(
                            encrypted_file, remote_key, verify=True, object_metadata=object_metadata
                        )
                        mirrored_offsite = True
                    except Exception as exc:
                        mirrored_offsite = False
                        offsite_error = str(exc).strip() or "Offsite mirror failed"
                        logger.error("Offsite mirror failed for %s: %s", remote_key, offsite_error)

                size = encrypted_file.stat().st_size
                logger.info(f"Backup completed: {remote_key} ({size} bytes)")

                # Step 5: Send to admin (sync)
                notification_sent = None
                notification_error = None
                if send_to_admin:
                    from .notification import send_backup_to_admin_sync

                    notification_result = send_backup_to_admin_sync(
                        file_path=encrypted_file,
                        backup_name=remote_key,
                        size=size,
                    )
                    notification_sent = notification_result.success
                    notification_error = notification_result.error
                    if not notification_result.success and notification_result.error:
                        logger.warning(notification_result.error)

                return BackupResult(
                    success=True,
                    backup_key=remote_key,
                    recovery_code=recovery_code,
                    format_version=format_version,
                    portable=portable,
                    key_fingerprint=self.encryption.key_fingerprint,
                    created_with_current_key=True,
                    size=size,
                    uploaded=True,
                    mirrored_offsite=mirrored_offsite,
                    offsite_error=offsite_error,
                    notification_sent=notification_sent,
                    notification_error=notification_error,
                )

            except Exception as e:
                import traceback

                tb_text = traceback.format_exc()
                logger.error(f"Backup failed: {e}\n{tb_text}")
                from .notification import notify_backup_failure_sync

                if notify_on_failure:
                    notify_result = notify_backup_failure_sync(str(e), traceback_text=tb_text)
                    if not notify_result.success and notify_result.error:
                        logger.warning(notify_result.error)
                return BackupResult(success=False, error=str(e))

    def _pg_dump_sync(self, output_path: Path) -> None:
        """Синхронный pg_dump для Celery."""
        import os
        import subprocess

        pgpass_path = output_path.parent / ".pgpass"
        pgpass_content = (
            f"{settings.POSTGRES_SERVER}:"
            f"{settings.POSTGRES_PORT}:"
            f"{settings.POSTGRES_DB}:"
            f"{settings.POSTGRES_USER}:"
            f"{settings.POSTGRES_PASSWORD}"
        )

        try:
            pgpass_path.write_text(pgpass_content)
            os.chmod(pgpass_path, 0o600)

            cmd = [
                "pg_dump",
                "--format=custom",
                "--no-password",
                f"--host={settings.POSTGRES_SERVER}",
                f"--port={settings.POSTGRES_PORT}",
                f"--username={settings.POSTGRES_USER}",
                f"--dbname={settings.POSTGRES_DB}",
                f"--file={output_path}",
            ]

            env = {**dict(os.environ), "PGPASSFILE": str(pgpass_path)}

            result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=BACKUP_DUMP_TIMEOUT_SECONDS)

            if result.returncode != 0:
                raise RuntimeError(f"pg_dump failed: {result.stderr}")

            logger.info(f"pg_dump completed: {output_path.stat().st_size} bytes")

        finally:
            if pgpass_path.exists():
                pgpass_path.unlink()

    def list_backups_sync(self) -> list[BackupMetadata]:
        """Синхронный list_backups для Celery."""
        return self.storage.list_backups_sync()

    def delete_backup_sync(self, backup_key: str) -> bool:
        """Синхронное удаление бэкапа для Celery."""
        try:
            self.storage.delete_sync(backup_key)
            if self.offsite_storage:
                try:
                    self.offsite_storage.delete_sync(backup_key)
                except Exception as exc:
                    logger.warning("Failed to delete offsite backup %s: %s", backup_key, exc)
            return True
        except Exception as exc:
            logger.error("Delete failed: %s", exc)
            return False

    def cleanup_old_backups_sync(self, retention_days: int = None) -> int:
        """Синхронный cleanup для Celery."""
        from app.core.time_constants import BACKUP_RETENTION_DAYS

        retention = retention_days or BACKUP_RETENTION_DAYS
        cutoff = datetime.now().timestamp() - (retention * 86400)

        backups = self.list_backups_sync()
        deleted = 0

        for backup in backups:
            if backup.created_at.timestamp() < cutoff:
                if self.delete_backup_sync(backup.key):
                    deleted += 1
                    logger.info(f"Deleted old backup: {backup.key}")

        return deleted
