"""
Backup restoration service.
Handles download, decryption, decompression, and pg_restore.
"""
import asyncio
import gzip
import logging
import tempfile
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from app.core.config import settings
from .encryption import BackupEncryption
from .remote_storage import BackupStorage

logger = logging.getLogger(__name__)


@dataclass
class RestoreResult:
    """Result of restore operation."""
    success: bool
    error: Optional[str] = None


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
        with gzip.open(input_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                while chunk := f_in.read(64 * 1024):
                    f_out.write(chunk)
        
        logger.info(f"Decompressed: {input_path.stat().st_size} -> {output_path.stat().st_size}")
    
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
            cmd.append("--clean")
        
        cmd.append(str(dump_path))
        
        env = {"PGPASSWORD": settings.POSTGRES_PASSWORD}
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            env={**dict(__import__('os').environ), **env},
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        _, stderr = await proc.communicate()
        
        # pg_restore returns non-zero for warnings too, check stderr
        if proc.returncode != 0:
            stderr_text = stderr.decode()
            # Ignore "already exists" warnings
            if "ERROR" in stderr_text and "already exists" not in stderr_text:
                raise RuntimeError(f"pg_restore failed: {stderr_text}")
            logger.warning(f"pg_restore warnings: {stderr_text}")
        
        logger.info("pg_restore completed")
    
    async def verify_backup(self, backup_key: str) -> bool:
        """
        Verify backup integrity without full restore.
        Downloads and decrypts to verify, but doesn't restore.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            encrypted_file = tmp_path / "backup.enc"
            compressed_file = tmp_path / "backup.dump.gz"
            
            try:
                await self.storage.download(backup_key, encrypted_file)
                
                if not self.encryption.verify_file(encrypted_file):
                    return False
                
                # Try decryption
                self.encryption.decrypt_file(encrypted_file, compressed_file)
                
                # Verify gzip header
                with gzip.open(compressed_file, 'rb') as f:
                    f.read(1)  # Just check it opens
                
                return True
                
            except Exception as e:
                logger.error(f"Verification failed: {e}")
                return False
