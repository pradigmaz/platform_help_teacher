"""
Backup restore and verification orchestration.
"""

import logging
import tempfile
from pathlib import Path

from cryptography.exceptions import InvalidTag

from app.core.config import settings

from .compression import decompress_file
from .dump_runner import PostgresConnectionConfig, default_postgres_connection, run_pg_restore, verify_dump
from .encryption import (
    BackupEncryption,
    BackupFileInfo,
    InvalidRecoveryCodeError,
    RecoveryCodeRequiredError,
)
from .remote_storage import BackupStorage, get_offsite_storage
from .results import (
    VERIFY_STATUS_ARCHIVE_CORRUPTED,
    VERIFY_STATUS_DECRYPTION_FAILED,
    VERIFY_STATUS_DOWNLOAD_FAILED,
    VERIFY_STATUS_DUMP_INVALID,
    VERIFY_STATUS_FILE_CORRUPTED,
    VERIFY_STATUS_INVALID_RECOVERY_CODE,
    VERIFY_STATUS_RECOVERY_CODE_REQUIRED,
    VERIFY_STATUS_VALID,
    RestoreResult,
    VerifyResult,
    build_restore_result,
    build_verify_result,
)

logger = logging.getLogger(__name__)


class RestoreService:
    """Service for restoring encrypted PostgreSQL backups."""

    def __init__(self):
        self.encryption = BackupEncryption(settings.BACKUP_ENCRYPTION_KEY)
        self.storage = BackupStorage()
        self.offsite_storage = get_offsite_storage()

    async def restore_backup(
        self,
        backup_key: str,
        drop_existing: bool = False,
        recovery_code: str | None = None,
    ) -> RestoreResult:
        return await self.restore_backup_to_target(
            backup_key,
            target=default_postgres_connection(),
            drop_existing=drop_existing,
            recovery_code=recovery_code,
        )

    async def restore_backup_to_target(
        self,
        backup_key: str,
        *,
        target: PostgresConnectionConfig,
        drop_existing: bool = False,
        recovery_code: str | None = None,
    ) -> RestoreResult:
        with tempfile.TemporaryDirectory() as tmpdir:
            encrypted_file = Path(tmpdir) / "backup.enc"
            try:
                offsite_used = await self._download_from_available_storage(backup_key, encrypted_file)
            except Exception as exc:
                return build_restore_result(
                    success=False,
                    status=VERIFY_STATUS_DOWNLOAD_FAILED,
                    current_key_fingerprint=self.encryption.key_fingerprint,
                    error=str(exc).strip() or "Failed to download backup",
                    offsite_used=None,
                )
            return await self._restore_downloaded_backup(
                encrypted_file=encrypted_file,
                backup_key=backup_key,
                offsite_used=offsite_used,
                recovery_code=recovery_code,
                target=target,
                drop_existing=drop_existing,
            )

    async def verify_local_backup(self, encrypted_file: Path, recovery_code: str | None = None) -> VerifyResult:
        file_info = self._inspect_file_safely(encrypted_file)
        if not self.encryption.verify_file(encrypted_file):
            return build_verify_result(
                valid=False,
                status=VERIFY_STATUS_FILE_CORRUPTED,
                current_key_fingerprint=self.encryption.key_fingerprint,
                error="Backup file corrupted",
                file_info=file_info,
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            compressed_file = Path(tmpdir) / "backup.dump.gz"
            dump_file = Path(tmpdir) / "backup.dump"
            try:
                self.encryption.decrypt_file(encrypted_file, compressed_file, recovery_code)
                decompress_file(compressed_file, dump_file)
                await self._verify_dump(dump_file)
                return build_verify_result(
                    valid=True,
                    status=VERIFY_STATUS_VALID,
                    current_key_fingerprint=self.encryption.key_fingerprint,
                    file_info=file_info,
                )
            except RecoveryCodeRequiredError as exc:
                return build_verify_result(
                    valid=False,
                    status=VERIFY_STATUS_RECOVERY_CODE_REQUIRED,
                    current_key_fingerprint=self.encryption.key_fingerprint,
                    error=str(exc),
                    file_info=file_info,
                )
            except InvalidRecoveryCodeError as exc:
                return build_verify_result(
                    valid=False,
                    status=VERIFY_STATUS_INVALID_RECOVERY_CODE,
                    current_key_fingerprint=self.encryption.key_fingerprint,
                    error=str(exc),
                    file_info=file_info,
                )
            except InvalidTag:
                return build_verify_result(
                    valid=False,
                    status=VERIFY_STATUS_DECRYPTION_FAILED,
                    current_key_fingerprint=self.encryption.key_fingerprint,
                    error="Backup cannot be decrypted: wrong BACKUP_ENCRYPTION_KEY or corrupted file",
                    file_info=file_info,
                )
            except (OSError, EOFError) as exc:
                return build_verify_result(
                    valid=False,
                    status=VERIFY_STATUS_ARCHIVE_CORRUPTED,
                    current_key_fingerprint=self.encryption.key_fingerprint,
                    error=str(exc).strip() or "Backup archive is corrupted",
                    file_info=file_info,
                )
            except RuntimeError as exc:
                return build_verify_result(
                    valid=False,
                    status=VERIFY_STATUS_DUMP_INVALID,
                    current_key_fingerprint=self.encryption.key_fingerprint,
                    error=str(exc).strip() or "Backup dump verification failed",
                    file_info=file_info,
                )
            except Exception as exc:
                return build_verify_result(
                    valid=False,
                    status=VERIFY_STATUS_DECRYPTION_FAILED,
                    current_key_fingerprint=self.encryption.key_fingerprint,
                    error=str(exc).strip() or "Backup verification failed",
                    file_info=file_info,
                )

    async def verify_backup(self, backup_key: str, recovery_code: str | None = None) -> VerifyResult:
        with tempfile.TemporaryDirectory() as tmpdir:
            encrypted_file = Path(tmpdir) / "backup.enc"
            try:
                offsite_used = await self._download_from_available_storage(backup_key, encrypted_file)
            except Exception as exc:
                return build_verify_result(
                    valid=False,
                    status=VERIFY_STATUS_DOWNLOAD_FAILED,
                    current_key_fingerprint=self.encryption.key_fingerprint,
                    error=str(exc).strip() or "Failed to download backup",
                    offsite_used=None,
                )
            result = await self.verify_local_backup(encrypted_file, recovery_code)
            result.offsite_used = offsite_used
            return result

    async def _restore_downloaded_backup(
        self,
        *,
        encrypted_file: Path,
        backup_key: str,
        offsite_used: bool,
        recovery_code: str | None,
        target: PostgresConnectionConfig,
        drop_existing: bool,
    ) -> RestoreResult:
        with tempfile.TemporaryDirectory() as tmpdir:
            compressed_file = Path(tmpdir) / "backup.dump.gz"
            dump_file = Path(tmpdir) / "backup.dump"
            file_info = self._inspect_file_safely(encrypted_file)
            try:
                if not self.encryption.verify_file(encrypted_file):
                    return build_restore_result(
                        success=False,
                        status=VERIFY_STATUS_FILE_CORRUPTED,
                        current_key_fingerprint=self.encryption.key_fingerprint,
                        error="Backup file corrupted",
                        file_info=file_info,
                        offsite_used=offsite_used,
                    )
                self.encryption.decrypt_file(encrypted_file, compressed_file, recovery_code)
                decompress_file(compressed_file, dump_file)
                await self._pg_restore(dump_file, target, drop_existing)
                logger.info("Restore completed: %s", backup_key)
                return build_restore_result(
                    success=True,
                    status="restored",
                    current_key_fingerprint=self.encryption.key_fingerprint,
                    file_info=file_info,
                    offsite_used=offsite_used,
                )
            except RecoveryCodeRequiredError as exc:
                return build_restore_result(
                    success=False,
                    status=VERIFY_STATUS_RECOVERY_CODE_REQUIRED,
                    current_key_fingerprint=self.encryption.key_fingerprint,
                    error=str(exc),
                    file_info=file_info,
                    offsite_used=offsite_used,
                )
            except InvalidRecoveryCodeError as exc:
                return build_restore_result(
                    success=False,
                    status=VERIFY_STATUS_INVALID_RECOVERY_CODE,
                    current_key_fingerprint=self.encryption.key_fingerprint,
                    error=str(exc),
                    file_info=file_info,
                    offsite_used=offsite_used,
                )
            except InvalidTag:
                return build_restore_result(
                    success=False,
                    status=VERIFY_STATUS_DECRYPTION_FAILED,
                    current_key_fingerprint=self.encryption.key_fingerprint,
                    error="Backup cannot be decrypted: wrong BACKUP_ENCRYPTION_KEY or corrupted file",
                    file_info=file_info,
                    offsite_used=offsite_used,
                )
            except (OSError, EOFError) as exc:
                return build_restore_result(
                    success=False,
                    status=VERIFY_STATUS_ARCHIVE_CORRUPTED,
                    current_key_fingerprint=self.encryption.key_fingerprint,
                    error=str(exc).strip() or "Backup archive is corrupted",
                    file_info=file_info,
                    offsite_used=offsite_used,
                )
            except RuntimeError as exc:
                return build_restore_result(
                    success=False,
                    status=VERIFY_STATUS_DUMP_INVALID,
                    current_key_fingerprint=self.encryption.key_fingerprint,
                    error=str(exc).strip() or "Restore failed",
                    file_info=file_info,
                    offsite_used=offsite_used,
                )
            except Exception as exc:
                return build_restore_result(
                    success=False,
                    status=VERIFY_STATUS_DECRYPTION_FAILED,
                    current_key_fingerprint=self.encryption.key_fingerprint,
                    error=str(exc).strip() or "restore failed without details",
                    file_info=file_info,
                    offsite_used=offsite_used,
                )

    async def _download_from_available_storage(self, backup_key: str, local_path: Path) -> bool:
        try:
            await self.storage.download(backup_key, local_path)
            return False
        except Exception as primary_exc:
            if not self.offsite_storage:
                raise primary_exc
            logger.warning("Primary storage download failed for %s: %s", backup_key, primary_exc)
            await self.offsite_storage.download(backup_key, local_path)
            return True

    def _inspect_file_safely(self, encrypted_file: Path) -> BackupFileInfo | None:
        try:
            return self.encryption.inspect_file(encrypted_file)
        except Exception as exc:
            logger.error("Backup inspection failed: %s", exc)
            return None

    async def _pg_restore(self, dump_path: Path, target: PostgresConnectionConfig, drop_existing: bool) -> None:
        await run_pg_restore(dump_path, target, drop_existing=drop_existing)

    async def _verify_dump(self, dump_path: Path) -> None:
        await verify_dump(dump_path)
