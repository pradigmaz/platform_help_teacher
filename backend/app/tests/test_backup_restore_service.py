"""
Tests for backup restore and verification flows.
"""

import gzip
import os
import shutil
import sys
import types
from pathlib import Path

import pytest

os.environ.setdefault("BACKUP_ENCRYPTION_KEY", "test_backup_master_key_for_restore_suite_123")
os.environ.setdefault("MINIO_ROOT_USER", "test")
os.environ.setdefault("MINIO_ROOT_PASSWORD", "test")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")
os.environ.setdefault("TELEGRAM_WEBHOOK_SECRET", "test")

if "aioboto3" not in sys.modules:
    aioboto3_stub = types.ModuleType("aioboto3")

    class Session:  # pragma: no cover - only needed to satisfy import-time dependency
        pass

    aioboto3_stub.Session = Session
    sys.modules["aioboto3"] = aioboto3_stub

from app.services.backup import restore_service as restore_module
from app.services.backup.restore_service import RestoreService


class LocalBackupStorage:
    """Test double that serves a prepared encrypted backup file."""

    def __init__(self, source_path: Path):
        self.source_path = source_path

    async def download(self, backup_key: str, local_path: Path) -> None:
        shutil.copyfile(self.source_path, local_path)


class FakeProcess:
    """Async subprocess result stub."""

    def __init__(self, returncode: int, stderr: bytes, stdout: bytes = b""):
        self.returncode = returncode
        self.stderr = stderr
        self.stdout = stdout

    async def communicate(self) -> tuple[bytes, bytes]:
        return self.stdout, self.stderr


def _write_encrypted_backup(
    tmp_path: Path,
    service: RestoreService,
    dump_bytes: bytes,
    *,
    truncate_gzip_bytes: int = 0,
) -> Path:
    compressed_file = tmp_path / "backup.dump.gz"
    encrypted_file = tmp_path / "backup.enc"

    compressed_bytes = gzip.compress(dump_bytes)
    if truncate_gzip_bytes:
        compressed_bytes = compressed_bytes[:-truncate_gzip_bytes]
    compressed_file.write_bytes(compressed_bytes)
    service.encryption.encrypt_file(compressed_file, encrypted_file)
    return encrypted_file


@pytest.mark.asyncio
async def test_verify_backup_rejects_truncated_gzip(tmp_path: Path):
    service = RestoreService()
    encrypted_file = _write_encrypted_backup(
        tmp_path,
        service,
        b"pg dump payload" * 64,
        truncate_gzip_bytes=1,
    )
    service.storage = LocalBackupStorage(encrypted_file)

    assert await service.verify_backup("broken.enc") is False


@pytest.mark.asyncio
async def test_restore_backup_fails_on_lowercase_pg_restore_error(monkeypatch, tmp_path: Path):
    service = RestoreService()
    encrypted_file = _write_encrypted_backup(tmp_path, service, b"pg dump payload" * 64)
    service.storage = LocalBackupStorage(encrypted_file)

    async def fake_create_subprocess_exec(*cmd, **kwargs):
        return FakeProcess(returncode=1, stderr=b"error: archive is corrupt")

    monkeypatch.setattr(restore_module.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    result = await service.restore_backup("broken.enc")

    assert result.success is False
    assert result.error is not None
    assert "error: archive is corrupt" in result.error
