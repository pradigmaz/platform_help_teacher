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

from app.core.config import settings
from app.core.time_constants import BACKUP_DUMP_TIMEOUT_SECONDS

from .encryption import BackupEncryption
from .remote_storage import BackupStorage

logger = logging.getLogger(__name__)


@dataclass
class RestoreResult:
    """Result of restore operation."""

    success: bool
    error: str | None = None


class RestoreService:
    """Service for restoring encrypted PostgreSQL backups."""

    def __init__(self):
        self.encryption = BackupEncryption(settings.BACKUP_ENCRYPTION_KEY)
        self.storage = BackupStorage()

    async def restore_backup(self, backup_key: str, drop_existing: bool = False) -> RestoreResult:
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

            try:
                # Step 1: Download
                logger.info(f"Downloading backup: {backup_key}")
                await self.storage.download(backup_key, encrypted_file)

                # Step 2: Verify
                if not self.encryption.verify_file(encrypted_file):
                    return RestoreResult(success=False, error="Backup file corrupted")

                # Step 3: Decrypt
                logger.info("Decrypting backup...")
                self.encryption.decrypt_file(encrypted_file, compressed_file)
                encrypted_file.unlink()

                # Step 4: Decompress
                logger.info("Decompressing backup...")
                self._decompress(compressed_file, dump_file)
                compressed_file.unlink()

                # Step 5: pg_restore
                logger.info("Restoring database...")
                await self._pg_restore(dump_file, drop_existing)

                logger.info(f"Restore completed: {backup_key}")
                return RestoreResult(success=True)

            except Exception as e:
                logger.error(f"Restore failed: {e}")
                return RestoreResult(success=False, error=str(e))

    def _decompress(self, input_path: Path, output_path: Path) -> None:
        """Decompress gzip file."""
        with gzip.open(input_path, "rb") as f_in, open(output_path, "wb") as f_out:
            while chunk := f_in.read(64 * 1024):
                f_out.write(chunk)

        logger.info(f"Decompressed: {input_path.stat().st_size} -> {output_path.stat().st_size}")

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

    async def verify_backup(self, backup_key: str) -> bool:
        """
        Verify backup integrity without full restore.
        Downloads, decrypts, fully decompresses, and validates dump structure.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            encrypted_file = tmp_path / "backup.enc"
            compressed_file = tmp_path / "backup.dump.gz"
            dump_file = tmp_path / "backup.dump"

            try:
                await self.storage.download(backup_key, encrypted_file)

                if not self.encryption.verify_file(encrypted_file):
                    return False

                self.encryption.decrypt_file(encrypted_file, compressed_file)
                self._decompress(compressed_file, dump_file)
                await self._verify_dump(dump_file)
                return True

            except Exception as e:
                logger.error(f"Verification failed: {e}")
                return False
