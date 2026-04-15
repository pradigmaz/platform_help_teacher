"""
Backup creation orchestration.
"""

import logging
import tempfile
import traceback
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.core.time_constants import BACKUP_RETENTION_DAYS

from .artifact_ops import build_backup_object_metadata, generate_backup_name, secure_delete
from .compression import compress_file
from .dump_runner import default_postgres_connection, run_pg_dump, run_pg_dump_sync
from .encryption import BackupEncryption
from .notification import get_notification_service
from .notification_sync import notify_backup_failure_sync, send_backup_to_admin_sync
from .remote_storage import BackupStorage, get_offsite_storage
from .results import BackupResult, build_backup_success_result
from .storage_utils import BackupMetadata
from .upload_flow import annotate_offsite_presence, mirror_backup_upload, mirror_backup_upload_sync

logger = logging.getLogger(__name__)


class BackupService:
    """Service for creating encrypted PostgreSQL backups."""

    def __init__(self):
        self.encryption = BackupEncryption(settings.BACKUP_ENCRYPTION_KEY)
        self.storage = BackupStorage()
        self.offsite_storage = get_offsite_storage()

    async def create_backup(
        self,
        name: str | None = None,
        send_to_admin: bool = True,
        notify_on_failure: bool = True,
    ) -> BackupResult:
        backup_name = name or generate_backup_name()
        remote_key = f"{backup_name}.enc"
        if await self.storage.exists(remote_key):
            return BackupResult(success=False, backup_key=remote_key, error="Backup with this name already exists")

        with tempfile.TemporaryDirectory() as tmpdir:
            dump_file = Path(tmpdir) / f"{backup_name}.dump"
            compressed_file = Path(tmpdir) / f"{backup_name}.dump.gz"
            encrypted_file = Path(tmpdir) / f"{backup_name}.enc"
            try:
                logger.info("Starting backup: %s", backup_name)
                await run_pg_dump(dump_file, default_postgres_connection())
                result = await self._finalize_backup_async(
                    dump_file=dump_file,
                    compressed_file=compressed_file,
                    encrypted_file=encrypted_file,
                    remote_key=remote_key,
                    send_to_admin=send_to_admin,
                )
                logger.info("Backup completed: %s (%s bytes)", remote_key, result.size)
                return result
            except Exception as exc:
                return await self._handle_backup_failure_async(exc, notify_on_failure)

    async def list_backups(self) -> list[BackupMetadata]:
        return await annotate_offsite_presence(await self.storage.list_backups(), self.offsite_storage)

    async def delete_backup(self, backup_key: str) -> bool:
        try:
            await self.storage.delete(backup_key)
            if self.offsite_storage:
                try:
                    await self.offsite_storage.delete(backup_key)
                except Exception as exc:
                    logger.warning("Failed to delete offsite backup %s: %s", backup_key, exc)
            return True
        except Exception as exc:
            logger.error("Delete failed: %s", exc)
            return False

    async def cleanup_old_backups(self, retention_days: int | None = None) -> int:
        cutoff = datetime.now().timestamp() - ((retention_days or BACKUP_RETENTION_DAYS) * 86400)
        deleted = 0
        for backup in await self.list_backups():
            if backup.created_at.timestamp() < cutoff and await self.delete_backup(backup.key):
                deleted += 1
                logger.info("Deleted old backup: %s", backup.key)
        return deleted

    def create_backup_sync(
        self,
        name: str | None = None,
        send_to_admin: bool = True,
        notify_on_failure: bool = True,
    ) -> BackupResult:
        backup_name = name or generate_backup_name()
        remote_key = f"{backup_name}.enc"
        if self.storage.exists_sync(remote_key):
            return BackupResult(success=False, backup_key=remote_key, error="Backup with this name already exists")

        with tempfile.TemporaryDirectory() as tmpdir:
            dump_file = Path(tmpdir) / f"{backup_name}.dump"
            compressed_file = Path(tmpdir) / f"{backup_name}.dump.gz"
            encrypted_file = Path(tmpdir) / f"{backup_name}.enc"
            try:
                logger.info("Starting backup: %s", backup_name)
                run_pg_dump_sync(dump_file, default_postgres_connection())
                result = self._finalize_backup_sync(
                    dump_file=dump_file,
                    compressed_file=compressed_file,
                    encrypted_file=encrypted_file,
                    remote_key=remote_key,
                    send_to_admin=send_to_admin,
                )
                logger.info("Backup completed: %s (%s bytes)", remote_key, result.size)
                return result
            except Exception as exc:
                return self._handle_backup_failure_sync(exc, notify_on_failure)

    def list_backups_sync(self) -> list[BackupMetadata]:
        return self.storage.list_backups_sync()

    def delete_backup_sync(self, backup_key: str) -> bool:
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

    def cleanup_old_backups_sync(self, retention_days: int | None = None) -> int:
        cutoff = datetime.now().timestamp() - ((retention_days or BACKUP_RETENTION_DAYS) * 86400)
        deleted = 0
        for backup in self.list_backups_sync():
            if backup.created_at.timestamp() < cutoff and self.delete_backup_sync(backup.key):
                deleted += 1
                logger.info("Deleted old backup: %s", backup.key)
        return deleted

    async def _finalize_backup_async(
        self,
        *,
        dump_file: Path,
        compressed_file: Path,
        encrypted_file: Path,
        remote_key: str,
        send_to_admin: bool,
    ) -> BackupResult:
        recovery_code, metadata = self._encrypt_artifact(dump_file, compressed_file, encrypted_file)
        await self.storage.upload(encrypted_file, remote_key, object_metadata=metadata)
        mirrored_offsite, offsite_error = await mirror_backup_upload(
            encrypted_file,
            remote_key,
            metadata,
            self.offsite_storage,
        )
        size = encrypted_file.stat().st_size
        notification_sent, notification_error = await self._notify_backup_async(
            encrypted_file,
            remote_key,
            size,
            recovery_code,
            send_to_admin,
        )
        return build_backup_success_result(
            remote_key=remote_key,
            recovery_code=recovery_code,
            format_version=self.encryption.current_format_version,
            key_fingerprint=self.encryption.key_fingerprint,
            size=size,
            mirrored_offsite=mirrored_offsite,
            offsite_error=offsite_error,
            notification_sent=notification_sent,
            notification_error=notification_error,
        )

    def _finalize_backup_sync(
        self,
        *,
        dump_file: Path,
        compressed_file: Path,
        encrypted_file: Path,
        remote_key: str,
        send_to_admin: bool,
    ) -> BackupResult:
        recovery_code, metadata = self._encrypt_artifact(dump_file, compressed_file, encrypted_file)
        self.storage.upload_sync(encrypted_file, remote_key, verify=True, object_metadata=metadata)
        mirrored_offsite, offsite_error = mirror_backup_upload_sync(
            encrypted_file,
            remote_key,
            metadata,
            self.offsite_storage,
        )
        size = encrypted_file.stat().st_size
        notification_sent, notification_error = self._notify_backup_sync(
            encrypted_file,
            remote_key,
            size,
            recovery_code,
            send_to_admin,
        )
        return build_backup_success_result(
            remote_key=remote_key,
            recovery_code=recovery_code,
            format_version=self.encryption.current_format_version,
            key_fingerprint=self.encryption.key_fingerprint,
            size=size,
            mirrored_offsite=mirrored_offsite,
            offsite_error=offsite_error,
            notification_sent=notification_sent,
            notification_error=notification_error,
        )

    def _encrypt_artifact(
        self,
        dump_file: Path,
        compressed_file: Path,
        encrypted_file: Path,
    ) -> tuple[str, dict[str, str]]:
        compress_file(dump_file, compressed_file)
        secure_delete(dump_file)
        recovery_code = self.encryption.encrypt_file(compressed_file, encrypted_file)
        secure_delete(compressed_file)
        return recovery_code, build_backup_object_metadata(
            self.encryption,
            format_version=self.encryption.current_format_version,
            portable=True,
        )

    async def _notify_backup_async(
        self,
        encrypted_file: Path,
        remote_key: str,
        size: int,
        recovery_code: str,
        send_to_admin: bool,
    ) -> tuple[bool | None, str | None]:
        if not send_to_admin:
            return None, None
        notification_result = await get_notification_service().send_backup_to_admin(
            file_path=encrypted_file,
            backup_name=remote_key,
            size=size,
            recovery_code=recovery_code,
        )
        if notification_result.error:
            logger.warning(notification_result.error)
        return notification_result.success, notification_result.error

    def _notify_backup_sync(
        self,
        encrypted_file: Path,
        remote_key: str,
        size: int,
        recovery_code: str,
        send_to_admin: bool,
    ) -> tuple[bool | None, str | None]:
        if not send_to_admin:
            return None, None
        notification_result = send_backup_to_admin_sync(
            file_path=encrypted_file,
            backup_name=remote_key,
            size=size,
            recovery_code=recovery_code,
        )
        if notification_result.error:
            logger.warning(notification_result.error)
        return notification_result.success, notification_result.error

    async def _handle_backup_failure_async(self, exc: Exception, notify_on_failure: bool) -> BackupResult:
        tb_text = traceback.format_exc()
        logger.error("Backup failed: %s\n%s", exc, tb_text)
        if notify_on_failure:
            notify_result = await get_notification_service().notify_backup_failure(str(exc), traceback_text=tb_text)
            if not notify_result.success and notify_result.error:
                logger.warning(notify_result.error)
        return BackupResult(success=False, error=str(exc))

    def _handle_backup_failure_sync(self, exc: Exception, notify_on_failure: bool) -> BackupResult:
        tb_text = traceback.format_exc()
        logger.error("Backup failed: %s\n%s", exc, tb_text)
        if notify_on_failure:
            notify_result = notify_backup_failure_sync(str(exc), traceback_text=tb_text)
            if not notify_result.success and notify_result.error:
                logger.warning(notify_result.error)
        return BackupResult(success=False, error=str(exc))
