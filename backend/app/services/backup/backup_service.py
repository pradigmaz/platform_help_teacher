"""
Backup creation service.
Handles pg_dump, compression, encryption, and upload.
"""
import asyncio
import gzip
import logging
import tempfile
import secrets
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass

from app.core.config import settings
from .encryption import BackupEncryption
from .remote_storage import BackupStorage, BackupMetadata
from .notification import get_notification_service

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
        with open(file_path, 'wb') as f:
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
    backup_key: Optional[str] = None
    size: Optional[int] = None
    error: Optional[str] = None


class BackupService:
    """Service for creating encrypted PostgreSQL backups."""
    
    def __init__(self):
        self.encryption = BackupEncryption(settings.BACKUP_ENCRYPTION_KEY)
        self.storage = BackupStorage()
    
    async def create_backup(
        self,
        name: Optional[str] = None,
        send_to_admin: bool = True,
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
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = name or _generate_backup_name()
        
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
                self.encryption.encrypt_file(compressed_file, encrypted_file)
                _secure_delete(compressed_file)  # Secure cleanup compressed
                
                # Step 4: Upload
                remote_key = f"{backup_name}.enc"
                await self.storage.upload(encrypted_file, remote_key)
                
                size = encrypted_file.stat().st_size
                logger.info(f"Backup completed: {remote_key} ({size} bytes)")
                
                # Step 5: Send to admin via Telegram
                if send_to_admin:
                    notifier = get_notification_service()
                    await notifier.send_backup_to_admin(
                        file_path=encrypted_file,
                        backup_name=remote_key,
                        size=size,
                    )
                
                return BackupResult(
                    success=True,
                    backup_key=remote_key,
                    size=size,
                )
                
            except Exception as e:
                import traceback
                tb_text = traceback.format_exc()
                logger.error(f"Backup failed: {e}\n{tb_text}")
                # Notify admin about failure with full traceback
                notifier = get_notification_service()
                await notifier.notify_backup_failure(str(e), traceback_text=tb_text)
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
            
            _, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                raise RuntimeError(f"pg_dump failed: {stderr.decode()}")
            
            logger.info(f"pg_dump completed: {output_path.stat().st_size} bytes")
            
        finally:
            # Always cleanup .pgpass
            if pgpass_path.exists():
                pgpass_path.unlink()
    
    def _compress(self, input_path: Path, output_path: Path) -> None:
        """Compress file using gzip."""
        with open(input_path, 'rb') as f_in:
            with gzip.open(output_path, 'wb', compresslevel=6) as f_out:
                while chunk := f_in.read(64 * 1024):
                    f_out.write(chunk)
        
        logger.info(f"Compressed: {input_path.stat().st_size} -> {output_path.stat().st_size}")
    
    async def list_backups(self) -> List[BackupMetadata]:
        """List all available backups."""
        return await self.storage.list_backups()
    
    async def delete_backup(self, backup_key: str) -> bool:
        """Delete a backup by key."""
        try:
            await self.storage.delete(backup_key)
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False
    
    async def cleanup_old_backups(self, retention_days: int = None) -> int:
        """Delete backups older than retention period."""
        retention = retention_days or settings.BACKUP_RETENTION_DAYS
        cutoff = datetime.now().timestamp() - (retention * 86400)
        
        backups = await self.list_backups()
        deleted = 0
        
        for backup in backups:
            if backup.created_at.timestamp() < cutoff:
                await self.storage.delete(backup.key)
                deleted += 1
                logger.info(f"Deleted old backup: {backup.key}")
        
        return deleted
