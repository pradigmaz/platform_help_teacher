"""
Backup restoration service.
Handles download, decryption, decompression, and pg_restore.
"""

import asyncio
import contextlib
import gzip
import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path

from cryptography.exceptions import InvalidTag

from app.core.config import settings
from app.core.time_constants import BACKUP_DUMP_TIMEOUT_SECONDS

from .encryption import (
    BackupEncryption,
    BackupFileInfo,
    InvalidRecoveryCodeError,
    RecoveryCodeRequiredError,
)
from .remote_storage import BackupStorage, get_offsite_storage

logger = logging.getLogger(__name__)

VERIFY_STATUS_VALID = "valid"
VERIFY_STATUS_DOWNLOAD_FAILED = "download_failed"
VERIFY_STATUS_FILE_CORRUPTED = "file_corrupted"
VERIFY_STATUS_RECOVERY_CODE_REQUIRED = "recovery_code_required"
VERIFY_STATUS_INVALID_RECOVERY_CODE = "invalid_recovery_code"
VERIFY_STATUS_DECRYPTION_FAILED = "decryption_failed"
VERIFY_STATUS_ARCHIVE_CORRUPTED = "archive_corrupted"
VERIFY_STATUS_DUMP_INVALID = "dump_invalid"


@dataclass
class RestoreResult:
    """Result of restore operation."""

    success: bool
    error: str | None = None
    status: str | None = None
    format_version: int | None = None
    portable: bool | None = None
    created_with_current_key: bool | None = None
    offsite_used: bool | None = None


@dataclass
class VerifyResult:
    """Detailed backup verification result."""

    valid: bool
    status: str
    error: str | None = None
    format_version: int | None = None
    portable: bool | None = None
    created_with_current_key: bool | None = None
    offsite_used: bool | None = None


class RestoreService:
    """Service for restoring encrypted PostgreSQL backups."""

    def __init__(self):
        self.encryption = BackupEncryption(settings.BACKUP_ENCRYPTION_KEY)
        self.storage = BackupStorage()
        self.offsite_storage = get_offsite_storage()

    def _created_with_current_key(self, file_info: BackupFileInfo | None) -> bool | None:
        if not file_info or not file_info.key_fingerprint:
            return None
        return file_info.key_fingerprint == self.encryption.key_fingerprint

    def _build_verify_result(
        self,
        *,
        valid: bool,
        status: str,
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
            created_with_current_key=self._created_with_current_key(file_info),
            offsite_used=offsite_used,
        )

    def _build_restore_result(
        self,
        *,
        success: bool,
        status: str,
        error: str | None = None,
        file_info: BackupFileInfo | None = None,
        offsite_used: bool | None = None,
    ) -> RestoreResult:
        return RestoreResult(
            success=success,
            error=error,
            status=status,
            format_version=file_info.format_version if file_info else None,
            portable=file_info.portable if file_info else None,
            created_with_current_key=self._created_with_current_key(file_info),
            offsite_used=offsite_used,
        )

    def _inspect_file_safely(self, encrypted_file: Path) -> BackupFileInfo | None:
        try:
            return self.encryption.inspect_file(encrypted_file)
        except Exception as exc:
            logger.error("Backup inspection failed: %s", exc)
            return None

    async def _download_from_available_storage(self, backup_key: str, local_path: Path) -> bool:
        """Download backup from primary storage, then offsite mirror if available."""
        try:
            await self.storage.download(backup_key, local_path)
            return False
        except Exception as primary_exc:
            if not self.offsite_storage:
                raise primary_exc

            logger.warning("Primary storage download failed for %s: %s", backup_key, primary_exc)
            await self.offsite_storage.download(backup_key, local_path)
            return True

    async def restore_backup(
        self,
        backup_key: str,
        drop_existing: bool = False,
        recovery_code: str | None = None,
    ) -> RestoreResult:
        """
        Restore encrypted backup to PostgreSQL database.

        Steps:
        1. Download from remote storage
        2. Verify integrity
        3. AES-256-GCM decryption
        4. gunzip decompression
        5. pg_restore to database
        6. Cleanup temp files

        WARNING: This will overwrite existing data!
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            encrypted_file = tmp_path / "backup.enc"
            compressed_file = tmp_path / "backup.dump.gz"
            dump_file = tmp_path / "backup.dump"

            file_info: BackupFileInfo | None = None
            offsite_used = False

            try:
                logger.info("Downloading backup: %s", backup_key)
                try:
                    offsite_used = await self._download_from_available_storage(backup_key, encrypted_file)
                except Exception as exc:
                    message = str(exc).strip() or "Failed to download backup"
                    logger.error("Restore failed: %s", message)
                    return self._build_restore_result(
                        success=False,
                        status=VERIFY_STATUS_DOWNLOAD_FAILED,
                        error=message,
                        file_info=None,
                        offsite_used=None,
                    )
                file_info = self._inspect_file_safely(encrypted_file)

                if not self.encryption.verify_file(encrypted_file):
                    return self._build_restore_result(
                        success=False,
                        status=VERIFY_STATUS_FILE_CORRUPTED,
                        error="Backup file corrupted",
                        file_info=file_info,
                        offsite_used=offsite_used,
                    )

                logger.info("Decrypting backup...")
                self.encryption.decrypt_file(encrypted_file, compressed_file, recovery_code)
                encrypted_file.unlink()

                logger.info("Decompressing backup...")
                self._decompress(compressed_file, dump_file)
                compressed_file.unlink()

                logger.info("Restoring database...")
                await self._pg_restore(dump_file, drop_existing)

                logger.info("Restore completed: %s", backup_key)
                return self._build_restore_result(
                    success=True,
                    status="restored",
                    file_info=file_info,
                    offsite_used=offsite_used,
                )

            except RecoveryCodeRequiredError as exc:
                message = str(exc)
                logger.error(message)
                return self._build_restore_result(
                    success=False,
                    status=VERIFY_STATUS_RECOVERY_CODE_REQUIRED,
                    error=message,
                    file_info=file_info,
                    offsite_used=offsite_used,
                )
            except InvalidRecoveryCodeError as exc:
                message = str(exc)
                logger.error(message)
                return self._build_restore_result(
                    success=False,
                    status=VERIFY_STATUS_INVALID_RECOVERY_CODE,
                    error=message,
                    file_info=file_info,
                    offsite_used=offsite_used,
                )
            except InvalidTag:
                message = "Backup cannot be decrypted: wrong BACKUP_ENCRYPTION_KEY or corrupted file"
                logger.error(message)
                return self._build_restore_result(
                    success=False,
                    status=VERIFY_STATUS_DECRYPTION_FAILED,
                    error=message,
                    file_info=file_info,
                    offsite_used=offsite_used,
                )
            except (gzip.BadGzipFile, EOFError, OSError) as exc:
                message = str(exc).strip() or "Backup archive is corrupted"
                logger.error("Restore failed: %s", message)
                return self._build_restore_result(
                    success=False,
                    status=VERIFY_STATUS_ARCHIVE_CORRUPTED,
                    error=message,
                    file_info=file_info,
                    offsite_used=offsite_used,
                )
            except RuntimeError as exc:
                message = str(exc).strip() or "Restore failed"
                logger.error("Restore failed: %s", message)
                return self._build_restore_result(
                    success=False,
                    status=VERIFY_STATUS_DUMP_INVALID,
                    error=message,
                    file_info=file_info,
                    offsite_used=offsite_used,
                )
            except Exception as exc:
                message = str(exc).strip() or f"{type(exc).__name__}: restore failed without details"
                logger.error("Restore failed: %s", message)
                return self._build_restore_result(
                    success=False,
                    status=VERIFY_STATUS_DECRYPTION_FAILED,
                    error=message,
                    file_info=file_info,
                    offsite_used=offsite_used,
                )

    def _decompress(self, input_path: Path, output_path: Path) -> None:
        """Decompress gzip file."""
        with gzip.open(input_path, "rb") as file_in, open(output_path, "wb") as file_out:
            while chunk := file_in.read(64 * 1024):
                file_out.write(chunk)

        logger.info("Decompressed: %s -> %s", input_path.stat().st_size, output_path.stat().st_size)

    async def _run_subprocess(
        self,
        cmd: list[str],
        *,
        env: dict[str, str] | None = None,
        error_prefix: str,
    ) -> tuple[str, str]:
        """Run a subprocess with timeout and strict non-zero handling."""
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=BACKUP_DUMP_TIMEOUT_SECONDS)
        except TimeoutError as exc:
            with contextlib.suppress(ProcessLookupError):
                proc.kill()
            with contextlib.suppress(ProcessLookupError):
                await proc.wait()
            raise RuntimeError(f"{error_prefix} timed out after {BACKUP_DUMP_TIMEOUT_SECONDS} seconds") from exc

        stdout_text = stdout.decode(errors="replace")
        stderr_text = stderr.decode(errors="replace")

        if proc.returncode != 0:
            details = stderr_text.strip() or stdout_text.strip() or f"exit code {proc.returncode}"
            raise RuntimeError(f"{error_prefix} failed: {details}")

        return stdout_text, stderr_text

    async def _pg_restore(self, dump_path: Path, drop_existing: bool) -> None:
        """Execute pg_restore command."""
        cmd = [
            "pg_restore",
            "--no-password",
            f"--host={settings.POSTGRES_SERVER}",
            f"--port={settings.POSTGRES_PORT}",
            f"--username={settings.POSTGRES_USER}",
            f"--dbname={settings.POSTGRES_DB}",
            "--no-owner",
            "--no-privileges",
        ]

        if drop_existing:
            cmd.extend(["--clean", "--if-exists"])

        cmd.append(str(dump_path))

        env = {"PGPASSWORD": settings.POSTGRES_PASSWORD}
        await self._run_subprocess(
            cmd,
            env={**dict(__import__("os").environ), **env},
            error_prefix="pg_restore",
        )
        logger.info("pg_restore completed")

    async def _verify_dump(self, dump_path: Path) -> None:
        """Verify that the dump is structurally readable by pg_restore."""
        await self._run_subprocess(["pg_restore", "--list", str(dump_path)], error_prefix="pg_restore --list")

    async def verify_local_backup(self, encrypted_file: Path, recovery_code: str | None = None) -> VerifyResult:
        """Verify an already downloaded local backup file."""
        file_info = self._inspect_file_safely(encrypted_file)
        if not self.encryption.verify_file(encrypted_file):
            return self._build_verify_result(
                valid=False,
                status=VERIFY_STATUS_FILE_CORRUPTED,
                error="Backup file corrupted",
                file_info=file_info,
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            compressed_file = tmp_path / "backup.dump.gz"
            dump_file = tmp_path / "backup.dump"

            try:
                self.encryption.decrypt_file(encrypted_file, compressed_file, recovery_code)
                self._decompress(compressed_file, dump_file)
                await self._verify_dump(dump_file)
                return self._build_verify_result(
                    valid=True,
                    status=VERIFY_STATUS_VALID,
                    file_info=file_info,
                )
            except RecoveryCodeRequiredError as exc:
                message = str(exc)
                logger.error(message)
                return self._build_verify_result(
                    valid=False,
                    status=VERIFY_STATUS_RECOVERY_CODE_REQUIRED,
                    error=message,
                    file_info=file_info,
                )
            except InvalidRecoveryCodeError as exc:
                message = str(exc)
                logger.error(message)
                return self._build_verify_result(
                    valid=False,
                    status=VERIFY_STATUS_INVALID_RECOVERY_CODE,
                    error=message,
                    file_info=file_info,
                )
            except InvalidTag:
                message = "Backup cannot be decrypted: wrong BACKUP_ENCRYPTION_KEY or corrupted file"
                logger.error(message)
                return self._build_verify_result(
                    valid=False,
                    status=VERIFY_STATUS_DECRYPTION_FAILED,
                    error=message,
                    file_info=file_info,
                )
            except (gzip.BadGzipFile, EOFError, OSError) as exc:
                message = str(exc).strip() or "Backup archive is corrupted"
                logger.error("Verification failed: %s", message)
                return self._build_verify_result(
                    valid=False,
                    status=VERIFY_STATUS_ARCHIVE_CORRUPTED,
                    error=message,
                    file_info=file_info,
                )
            except RuntimeError as exc:
                message = str(exc).strip() or "Backup dump verification failed"
                logger.error("Verification failed: %s", message)
                return self._build_verify_result(
                    valid=False,
                    status=VERIFY_STATUS_DUMP_INVALID,
                    error=message,
                    file_info=file_info,
                )
            except Exception as exc:
                message = str(exc).strip() or "Backup verification failed"
                logger.error("Verification failed: %s", message)
                return self._build_verify_result(
                    valid=False,
                    status=VERIFY_STATUS_DECRYPTION_FAILED,
                    error=message,
                    file_info=file_info,
                )

    async def verify_backup(self, backup_key: str, recovery_code: str | None = None) -> VerifyResult:
        """
        Verify backup integrity without full restore.
        Downloads, decrypts, fully decompresses, and validates dump structure.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            encrypted_file = tmp_path / "backup.enc"

            try:
                offsite_used = await self._download_from_available_storage(backup_key, encrypted_file)
            except Exception as exc:
                message = str(exc).strip() or "Failed to download backup"
                logger.error("Verification failed: %s", message)
                return self._build_verify_result(
                    valid=False,
                    status=VERIFY_STATUS_DOWNLOAD_FAILED,
                    error=message,
                    offsite_used=None,
                )

            result = await self.verify_local_backup(encrypted_file, recovery_code)
            result.offsite_used = offsite_used
            return result
