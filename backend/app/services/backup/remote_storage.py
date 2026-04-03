"""
Remote storage abstraction for encrypted backups.
"""

import logging
import os
from pathlib import Path
from typing import Any

from aioboto3 import Session

from app.core.config import settings

from .storage_utils import (
    BackupMetadata,
    build_backup_metadata,
    compute_md5,
    normalize_endpoint,
    normalize_object_metadata,
    upload_verification_error,
)

logger = logging.getLogger(__name__)

_session: Session | None = None


def _get_session() -> Session:
    global _session
    if _session is None:
        _session = Session()
    return _session


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
        self.endpoint = normalize_endpoint(endpoint or settings.MINIO_ENDPOINT, default_scheme=default_scheme)
        self.access_key = access_key or settings.MINIO_ROOT_USER
        self.secret_key = secret_key or settings.MINIO_ROOT_PASSWORD
        self.label = label

    async def _get_client(self):
        return _get_session().client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

    def _get_sync_client(self):
        import boto3

        return boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

    async def ensure_bucket(self) -> None:
        async with await self._get_client() as client:
            try:
                await client.head_bucket(Bucket=self.bucket)
            except Exception:
                await client.create_bucket(Bucket=self.bucket)
                logger.info("Created %s backup bucket: %s", self.label, self.bucket)

    def ensure_bucket_sync(self) -> None:
        client = self._get_sync_client()
        try:
            client.head_bucket(Bucket=self.bucket)
        except Exception:
            client.create_bucket(Bucket=self.bucket)
            logger.info("Created %s backup bucket: %s", self.label, self.bucket)

    async def exists(self, remote_key: str) -> bool:
        async with await self._get_client() as client:
            try:
                await client.head_object(Bucket=self.bucket, Key=remote_key)
                return True
            except Exception:
                return False

    def exists_sync(self, remote_key: str) -> bool:
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
        await self.ensure_bucket()
        async with await self._get_client() as client:
            await self._upload_with_client(
                client=client,
                local_path=local_path,
                remote_key=remote_key,
                verify=verify,
                object_metadata=object_metadata,
                delete_on_failure=True,
            )
        return remote_key

    def upload_sync(
        self,
        local_path: Path,
        remote_key: str,
        verify: bool = True,
        object_metadata: dict[str, str] | None = None,
    ) -> str:
        self.ensure_bucket_sync()
        self._upload_with_sync_client(
            client=self._get_sync_client(),
            local_path=local_path,
            remote_key=remote_key,
            verify=verify,
            object_metadata=object_metadata,
        )
        return remote_key

    async def _upload_with_client(
        self,
        *,
        client,
        local_path: Path,
        remote_key: str,
        verify: bool,
        object_metadata: dict[str, str] | None,
        delete_on_failure: bool,
    ) -> None:
        upload_kwargs: dict[str, Any] = {"Filename": str(local_path), "Bucket": self.bucket, "Key": remote_key}
        if object_metadata:
            upload_kwargs["ExtraArgs"] = {"Metadata": normalize_object_metadata(object_metadata)}
        await client.upload_file(**upload_kwargs)
        logger.info("Uploaded %s backup: %s", self.label, remote_key)

        if not verify:
            return

        local_md5 = compute_md5(local_path)
        response = await client.head_object(Bucket=self.bucket, Key=remote_key)
        error = upload_verification_error(response, local_path, local_md5)
        if error:
            if delete_on_failure:
                await client.delete_object(Bucket=self.bucket, Key=remote_key)
            raise RuntimeError(error)
        logger.info("Upload verified (%s): %s", self.label, remote_key)

    def _upload_with_sync_client(
        self,
        *,
        client,
        local_path: Path,
        remote_key: str,
        verify: bool,
        object_metadata: dict[str, str] | None,
    ) -> None:
        upload_kwargs: dict[str, Any] = {"Filename": str(local_path), "Bucket": self.bucket, "Key": remote_key}
        if object_metadata:
            upload_kwargs["ExtraArgs"] = {"Metadata": normalize_object_metadata(object_metadata)}
        client.upload_file(**upload_kwargs)
        logger.info("Uploaded %s backup: %s", self.label, remote_key)

        if not verify:
            return

        self._verify_uploaded_object_sync(
            remote_key,
            local_path,
            client.head_object(Bucket=self.bucket, Key=remote_key),
            compute_md5(local_path),
            lambda: client.delete_object(Bucket=self.bucket, Key=remote_key),
        )

    def _verify_uploaded_object_sync(self, remote_key: str, local_path: Path, response: dict, local_md5: str, delete_callback) -> None:
        error = upload_verification_error(response, local_path, local_md5)
        if error:
            delete_callback()
            raise RuntimeError(error)
        logger.info("Upload verified (%s): %s", self.label, remote_key)

    async def download(self, remote_key: str, local_path: Path) -> None:
        async with await self._get_client() as client:
            await client.download_file(self.bucket, remote_key, str(local_path))
            logger.info("Downloaded %s backup: %s", self.label, remote_key)

    async def list_backups(self) -> list[BackupMetadata]:
        await self.ensure_bucket()
        backups: list[BackupMetadata] = []
        async with await self._get_client() as client:
            paginator = client.get_paginator("list_objects_v2")
            async for page in paginator.paginate(Bucket=self.bucket):
                for obj in page.get("Contents", []):
                    head = await client.head_object(Bucket=self.bucket, Key=obj["Key"])
                    backups.append(
                        build_backup_metadata(
                            obj["Key"],
                            size=obj["Size"],
                            created_at=obj["LastModified"],
                            etag=head.get("ETag", "").strip('"') or None,
                            raw_metadata=head.get("Metadata"),
                        )
                    )
        return sorted(backups, key=lambda item: item.created_at, reverse=True)

    def list_backups_sync(self) -> list[BackupMetadata]:
        self.ensure_bucket_sync()
        client = self._get_sync_client()
        backups: list[BackupMetadata] = []
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket):
            for obj in page.get("Contents", []):
                head = client.head_object(Bucket=self.bucket, Key=obj["Key"])
                backups.append(
                    build_backup_metadata(
                        obj["Key"],
                        size=obj["Size"],
                        created_at=obj["LastModified"],
                        etag=head.get("ETag", "").strip('"') or None,
                        raw_metadata=head.get("Metadata"),
                    )
                )
        return sorted(backups, key=lambda item: item.created_at, reverse=True)

    async def delete(self, remote_key: str) -> None:
        async with await self._get_client() as client:
            await client.delete_object(Bucket=self.bucket, Key=remote_key)
            logger.info("Deleted %s backup: %s", self.label, remote_key)

    def delete_sync(self, remote_key: str) -> None:
        client = self._get_sync_client()
        client.delete_object(Bucket=self.bucket, Key=remote_key)
        logger.info("Deleted %s backup: %s", self.label, remote_key)

    async def get_metadata(self, remote_key: str) -> BackupMetadata | None:
        async with await self._get_client() as client:
            try:
                response = await client.head_object(Bucket=self.bucket, Key=remote_key)
                return build_backup_metadata(
                    remote_key,
                    size=response["ContentLength"],
                    created_at=response["LastModified"],
                    etag=response.get("ETag", "").strip('"') or None,
                    raw_metadata=response.get("Metadata"),
                )
            except Exception:
                return None


def get_offsite_storage() -> BackupStorage | None:
    endpoint = os.getenv("BACKUP_OFFSITE_ENDPOINT", "").strip()
    access_key = os.getenv("BACKUP_OFFSITE_ACCESS_KEY", "").strip()
    secret_key = os.getenv("BACKUP_OFFSITE_SECRET_KEY", "").strip()
    bucket = os.getenv("BACKUP_OFFSITE_BUCKET", "").strip()
    if not all((endpoint, access_key, secret_key, bucket)):
        return None
    return BackupStorage(
        bucket=bucket,
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        label="offsite",
        default_scheme="https",
    )
