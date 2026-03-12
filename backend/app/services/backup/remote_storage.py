"""
Remote storage abstraction for backups.
Supports MinIO/S3 (reuses existing StorageService pattern).
"""

import hashlib
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from aioboto3 import Session

from app.core.config import settings

logger = logging.getLogger(__name__)

_session: Session | None = None

BACKUP_METADATA_FORMAT_VERSION = "backup-format-version"
BACKUP_METADATA_PORTABLE = "backup-portable"
BACKUP_METADATA_KEY_FINGERPRINT = "backup-key-fingerprint"


def _get_session() -> Session:
    """Get or create singleton aioboto3 session."""
    global _session
    if _session is None:
        _session = Session()
    return _session


def _compute_md5(file_path: Path) -> str:
    """Compute MD5 hash of file for integrity verification."""
    md5 = hashlib.md5()
    with open(file_path, "rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(64 * 1024), b""):
            md5.update(chunk)
    return md5.hexdigest()


def _normalize_endpoint(endpoint: str, default_scheme: str = "http") -> str:
    endpoint = endpoint.strip()
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        return endpoint
    return f"{default_scheme}://{endpoint}"


def _normalize_object_metadata(metadata: dict[str, str] | None) -> dict[str, str]:
    if not metadata:
        return {}
    return {str(key).lower(): str(value) for key, value in metadata.items() if value is not None}


def _parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False
    return None


@dataclass(frozen=True)
class BackupObjectMetadata:
    """Parsed backup-specific object metadata."""

    format_version: int | None = None
    portable: bool | None = None
    key_fingerprint: str | None = None
    created_with_current_key: bool | None = None


@dataclass
class BackupMetadata:
    """Backup file metadata."""

    name: str
    size: int
    created_at: datetime
    key: str
    etag: str | None = None
    format_version: int | None = None
    portable: bool | None = None
    key_fingerprint: str | None = None
    created_with_current_key: bool | None = None
    offsite_present: bool | None = None


class BackupStorage:
    """Remote storage for encrypted backups."""

    def __init__(
        self,
        bucket: str | None = None,
        *,
        endpoint: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        label: str = "primary",
        default_scheme: str = "http",
    ):
        self.bucket = bucket or settings.BACKUP_STORAGE_BUCKET
        self.endpoint = _normalize_endpoint(endpoint or settings.MINIO_ENDPOINT, default_scheme=default_scheme)
        self.access_key = access_key or settings.MINIO_ROOT_USER
        self.secret_key = secret_key or settings.MINIO_ROOT_PASSWORD
        self.label = label

    async def _get_client(self):
        """Get S3 client context manager."""
        session = _get_session()
        return session.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

    def _get_sync_client(self):
        """Get synchronous boto3 client."""
        import boto3

        return boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

    def _build_backup_metadata(
        self,
        remote_key: str,
        size: int,
        created_at: datetime,
        etag: str | None = None,
        raw_metadata: dict[str, str] | None = None,
    ) -> BackupMetadata:
        parsed = self._parse_backup_object_metadata(raw_metadata)
        return BackupMetadata(
            name=Path(remote_key).stem,
            size=size,
            created_at=created_at,
            key=remote_key,
            etag=etag,
            format_version=parsed.format_version,
            portable=parsed.portable,
            key_fingerprint=parsed.key_fingerprint,
            created_with_current_key=parsed.created_with_current_key,
        )

    def _parse_backup_object_metadata(self, raw_metadata: dict[str, str] | None) -> BackupObjectMetadata:
        metadata = _normalize_object_metadata(raw_metadata)
        format_version = metadata.get(BACKUP_METADATA_FORMAT_VERSION)
        key_fingerprint = metadata.get(BACKUP_METADATA_KEY_FINGERPRINT)
        parsed_format_version = int(format_version) if format_version and format_version.isdigit() else None
        portable = _parse_bool(metadata.get(BACKUP_METADATA_PORTABLE))
        created_with_current_key = None
        if key_fingerprint:
            created_with_current_key = (
                key_fingerprint == hashlib.sha256(settings.BACKUP_ENCRYPTION_KEY.encode()).digest()[:8].hex()
            )
        return BackupObjectMetadata(
            format_version=parsed_format_version,
            portable=portable,
            key_fingerprint=key_fingerprint,
            created_with_current_key=created_with_current_key,
        )

    async def ensure_bucket(self) -> None:
        """Create bucket if not exists."""
        async with await self._get_client() as client:
            try:
                await client.head_bucket(Bucket=self.bucket)
            except Exception:
                await client.create_bucket(Bucket=self.bucket)
                logger.info("Created %s backup bucket: %s", self.label, self.bucket)

    def ensure_bucket_sync(self) -> None:
        """Create bucket if not exists (sync)."""
        client = self._get_sync_client()
        try:
            client.head_bucket(Bucket=self.bucket)
        except Exception:
            client.create_bucket(Bucket=self.bucket)
            logger.info("Created %s backup bucket: %s", self.label, self.bucket)

    async def exists(self, remote_key: str) -> bool:
        """Check whether backup object already exists."""
        async with await self._get_client() as client:
            try:
                await client.head_object(Bucket=self.bucket, Key=remote_key)
                return True
            except Exception:
                return False

    def exists_sync(self, remote_key: str) -> bool:
        """Check whether backup object already exists (sync)."""
        client = self._get_sync_client()
        try:
            client.head_object(Bucket=self.bucket, Key=remote_key)
            return True
        except Exception:
            return False

    async def upload(
        self,
        local_path: Path,
        remote_key: str,
        verify: bool = True,
        object_metadata: dict[str, str] | None = None,
    ) -> str:
        """
        Upload encrypted backup to remote storage.

        Args:
            local_path: Path to local file
            remote_key: S3 key for the file
            verify: If True, verify upload integrity via ETag/MD5
            object_metadata: Custom object metadata stored alongside the artifact

        Returns:
            remote_key on success

        Raises:
            RuntimeError: If verification fails
        """
        await self.ensure_bucket()

        local_md5 = _compute_md5(local_path) if verify else None
        extra_args = {"Metadata": _normalize_object_metadata(object_metadata)} if object_metadata else None

        async with await self._get_client() as client:
            upload_kwargs = {"Filename": str(local_path), "Bucket": self.bucket, "Key": remote_key}
            if extra_args:
                upload_kwargs["ExtraArgs"] = extra_args
            await client.upload_file(**upload_kwargs)
            logger.info("Uploaded %s backup: %s", self.label, remote_key)

            if verify:
                resp = await client.head_object(Bucket=self.bucket, Key=remote_key)
                remote_etag = resp.get("ETag", "").strip('"')
                is_multipart = "-" in remote_etag

                if is_multipart:
                    remote_size = resp.get("ContentLength", 0)
                    local_size = local_path.stat().st_size
                    if remote_size != local_size:
                        await client.delete_object(Bucket=self.bucket, Key=remote_key)
                        raise RuntimeError(f"Upload size mismatch: local={local_size}, remote={remote_size}")
                    logger.info("Upload verified (%s multipart, size check): %s", self.label, remote_key)
                elif remote_etag != local_md5:
                    await client.delete_object(Bucket=self.bucket, Key=remote_key)
                    raise RuntimeError(f"Upload verification failed: local={local_md5}, remote={remote_etag}")
                else:
                    logger.info("Upload verified (%s, MD5): %s", self.label, remote_key)

            return remote_key

    def upload_sync(
        self,
        local_path: Path,
        remote_key: str,
        verify: bool = True,
        object_metadata: dict[str, str] | None = None,
    ) -> str:
        """Upload backup (sync version for Celery)."""
        self.ensure_bucket_sync()
        client = self._get_sync_client()
        local_md5 = _compute_md5(local_path) if verify else None
        extra_args = {"Metadata": _normalize_object_metadata(object_metadata)} if object_metadata else None
        upload_kwargs = {"Filename": str(local_path), "Bucket": self.bucket, "Key": remote_key}
        if extra_args:
            upload_kwargs["ExtraArgs"] = extra_args
        client.upload_file(**upload_kwargs)
        logger.info("Uploaded %s backup: %s", self.label, remote_key)

        if verify:
            resp = client.head_object(Bucket=self.bucket, Key=remote_key)
            remote_etag = resp.get("ETag", "").strip('"')
            is_multipart = "-" in remote_etag

            if is_multipart:
                remote_size = resp.get("ContentLength", 0)
                local_size = local_path.stat().st_size
                if remote_size != local_size:
                    client.delete_object(Bucket=self.bucket, Key=remote_key)
                    raise RuntimeError(f"Upload size mismatch: local={local_size}, remote={remote_size}")
                logger.info("Upload verified (%s multipart, size check): %s", self.label, remote_key)
            elif remote_etag != local_md5:
                client.delete_object(Bucket=self.bucket, Key=remote_key)
                raise RuntimeError(f"Upload verification failed: local={local_md5}, remote={remote_etag}")
            else:
                logger.info("Upload verified (%s, MD5): %s", self.label, remote_key)

        return remote_key

    async def download(self, remote_key: str, local_path: Path) -> None:
        """Download encrypted backup from remote storage."""
        async with await self._get_client() as client:
            await client.download_file(self.bucket, remote_key, str(local_path))
            logger.info("Downloaded %s backup: %s", self.label, remote_key)

    async def list_backups(self) -> list[BackupMetadata]:
        """List all backups in storage."""
        await self.ensure_bucket()
        backups: list[BackupMetadata] = []
        async with await self._get_client() as client:
            paginator = client.get_paginator("list_objects_v2")
            async for page in paginator.paginate(Bucket=self.bucket):
                for obj in page.get("Contents", []):
                    head = await client.head_object(Bucket=self.bucket, Key=obj["Key"])
                    backups.append(
                        self._build_backup_metadata(
                            remote_key=obj["Key"],
                            size=obj["Size"],
                            created_at=obj["LastModified"],
                            etag=head.get("ETag", "").strip('"') or None,
                            raw_metadata=head.get("Metadata"),
                        )
                    )
        return sorted(backups, key=lambda item: item.created_at, reverse=True)

    def list_backups_sync(self) -> list[BackupMetadata]:
        """List all backups (sync version for Celery)."""
        self.ensure_bucket_sync()
        client = self._get_sync_client()
        backups: list[BackupMetadata] = []

        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket):
            for obj in page.get("Contents", []):
                head = client.head_object(Bucket=self.bucket, Key=obj["Key"])
                backups.append(
                    self._build_backup_metadata(
                        remote_key=obj["Key"],
                        size=obj["Size"],
                        created_at=obj["LastModified"],
                        etag=head.get("ETag", "").strip('"') or None,
                        raw_metadata=head.get("Metadata"),
                    )
                )
        return sorted(backups, key=lambda item: item.created_at, reverse=True)

    async def delete(self, remote_key: str) -> None:
        """Delete backup from remote storage."""
        async with await self._get_client() as client:
            await client.delete_object(Bucket=self.bucket, Key=remote_key)
            logger.info("Deleted %s backup: %s", self.label, remote_key)

    def delete_sync(self, remote_key: str) -> None:
        """Delete backup (sync version for Celery)."""
        client = self._get_sync_client()
        client.delete_object(Bucket=self.bucket, Key=remote_key)
        logger.info("Deleted %s backup: %s", self.label, remote_key)

    async def get_metadata(self, remote_key: str) -> BackupMetadata | None:
        """Get single backup metadata."""
        async with await self._get_client() as client:
            try:
                resp = await client.head_object(Bucket=self.bucket, Key=remote_key)
                return self._build_backup_metadata(
                    remote_key=remote_key,
                    size=resp["ContentLength"],
                    created_at=resp["LastModified"],
                    etag=resp.get("ETag", "").strip('"') or None,
                    raw_metadata=resp.get("Metadata"),
                )
            except Exception:
                return None


def get_offsite_storage() -> BackupStorage | None:
    """Return configured offsite mirror storage, if present."""
    endpoint = os.getenv("BACKUP_OFFSITE_ENDPOINT", "").strip()
    access_key = os.getenv("BACKUP_OFFSITE_ACCESS_KEY", "").strip()
    secret_key = os.getenv("BACKUP_OFFSITE_SECRET_KEY", "").strip()
    bucket = os.getenv("BACKUP_OFFSITE_BUCKET", "").strip()

    if not all((endpoint, access_key, secret_key, bucket)):
        return None

    default_scheme = "https"
    return BackupStorage(
        bucket=bucket,
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        label="offsite",
        default_scheme=default_scheme,
    )
