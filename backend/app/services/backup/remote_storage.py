"""
Remote storage abstraction for backups.
Supports MinIO/S3 (reuses existing StorageService pattern).
"""
import hashlib
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass
from aioboto3 import Session
from app.core.config import settings

logger = logging.getLogger(__name__)

_session: Session | None = None


def _get_session() -> Session:
    """Get or create singleton aioboto3 session."""
    global _session
    if _session is None:
        _session = Session()
    return _session


def _compute_md5(file_path: Path) -> str:
    """Compute MD5 hash of file for integrity verification."""
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(64 * 1024), b''):
            md5.update(chunk)
    return md5.hexdigest()


@dataclass
class BackupMetadata:
    """Backup file metadata."""
    name: str
    size: int
    created_at: datetime
    key: str
    etag: Optional[str] = None


class BackupStorage:
    """Remote storage for encrypted backups."""
    
    def __init__(self, bucket: str = None):
        self.bucket = bucket or settings.BACKUP_STORAGE_BUCKET
        self.endpoint = f"http://{settings.MINIO_ENDPOINT}"
    
    async def _get_client(self):
        """Get S3 client context manager."""
        session = _get_session()
        return session.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=settings.MINIO_ROOT_USER,
            aws_secret_access_key=settings.MINIO_ROOT_PASSWORD,
        )
    
    async def ensure_bucket(self) -> None:
        """Create bucket if not exists."""
        async with await self._get_client() as client:
            try:
                await client.head_bucket(Bucket=self.bucket)
            except Exception:
                await client.create_bucket(Bucket=self.bucket)
                logger.info(f"Created backup bucket: {self.bucket}")
    
    async def upload(self, local_path: Path, remote_key: str, verify: bool = True) -> str:
        """
        Upload encrypted backup to remote storage.
        
        Args:
            local_path: Path to local file
            remote_key: S3 key for the file
            verify: If True, verify upload integrity via ETag/MD5
        
        Returns:
            remote_key on success
            
        Raises:
            RuntimeError: If verification fails
        """
        await self.ensure_bucket()
        
        # Compute local MD5 before upload
        local_md5 = _compute_md5(local_path) if verify else None
        
        async with await self._get_client() as client:
            await client.upload_file(str(local_path), self.bucket, remote_key)
            logger.info(f"Uploaded backup: {remote_key}")
            
            # Verify upload integrity
            if verify:
                resp = await client.head_object(Bucket=self.bucket, Key=remote_key)
                # S3 ETag for non-multipart uploads is MD5 in quotes
                remote_etag = resp.get('ETag', '').strip('"')
                
                if remote_etag != local_md5:
                    # Cleanup corrupted upload
                    await client.delete_object(Bucket=self.bucket, Key=remote_key)
                    raise RuntimeError(
                        f"Upload verification failed: local={local_md5}, remote={remote_etag}"
                    )
                logger.info(f"Upload verified: {remote_key} (MD5: {local_md5})")
            
            return remote_key
    
    async def download(self, remote_key: str, local_path: Path) -> None:
        """Download encrypted backup from remote storage."""
        async with await self._get_client() as client:
            await client.download_file(self.bucket, remote_key, str(local_path))
            logger.info(f"Downloaded backup: {remote_key}")
    
    async def list_backups(self) -> List[BackupMetadata]:
        """List all backups in storage."""
        await self.ensure_bucket()
        backups = []
        async with await self._get_client() as client:
            paginator = client.get_paginator('list_objects_v2')
            async for page in paginator.paginate(Bucket=self.bucket):
                for obj in page.get('Contents', []):
                    backups.append(BackupMetadata(
                        name=Path(obj['Key']).stem,
                        size=obj['Size'],
                        created_at=obj['LastModified'],
                        key=obj['Key'],
                    ))
        return sorted(backups, key=lambda x: x.created_at, reverse=True)
    
    async def delete(self, remote_key: str) -> None:
        """Delete backup from remote storage."""
        async with await self._get_client() as client:
            await client.delete_object(Bucket=self.bucket, Key=remote_key)
            logger.info(f"Deleted backup: {remote_key}")
    
    async def get_metadata(self, remote_key: str) -> Optional[BackupMetadata]:
        """Get single backup metadata."""
        async with await self._get_client() as client:
            try:
                resp = await client.head_object(Bucket=self.bucket, Key=remote_key)
                return BackupMetadata(
                    name=Path(remote_key).stem,
                    size=resp['ContentLength'],
                    created_at=resp['LastModified'],
                    key=remote_key,
                )
            except Exception:
                return None
