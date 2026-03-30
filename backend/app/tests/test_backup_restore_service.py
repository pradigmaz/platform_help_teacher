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
from cryptography.exceptions import InvalidTag

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

from app.services.backup.encryption import BackupEncryption
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
) -> tuple[Path, str]:
    compressed_file = tmp_path / "backup.dump.gz"
    encrypted_file = tmp_path / "backup.enc"

    compressed_bytes = gzip.compress(dump_bytes)
    if truncate_gzip_bytes:
        compressed_bytes = compressed_bytes[:-truncate_gzip_bytes]
    compressed_file.write_bytes(compressed_bytes)
    recovery_code = service.encryption.encrypt_file(compressed_file, encrypted_file)
    return encrypted_file, recovery_code


@pytest.mark.asyncio
async def test_verify_backup_rejects_truncated_gzip(tmp_path: Path):
    service = RestoreService()
    encrypted_file, _ = _write_encrypted_backup(
        tmp_path,
        service,
        b"pg dump payload" * 64,
        truncate_gzip_bytes=1,
    )
    service.storage = LocalBackupStorage(encrypted_file)

    result = await service.verify_backup("broken.enc")
    assert result.valid is False
    assert result.status == "archive_corrupted"
    assert result.format_version == 3
    assert result.portable is True


@pytest.mark.asyncio
async def test_restore_backup_fails_on_lowercase_pg_restore_error(monkeypatch, tmp_path: Path):
    service = RestoreService()
    encrypted_file, _ = _write_encrypted_backup(tmp_path, service, b"pg dump payload" * 64)
    service.storage = LocalBackupStorage(encrypted_file)

    async def fake_pg_restore(dump_path: Path, target, drop_existing: bool) -> None:
        raise RuntimeError("pg_restore failed: error: archive is corrupt")

    monkeypatch.setattr(service, "_pg_restore", fake_pg_restore)

    result = await service.restore_backup("broken.enc")

    assert result.success is False
    assert result.error is not None
    assert result.status == "dump_invalid"
    assert "error: archive is corrupt" in result.error


@pytest.mark.asyncio
async def test_restore_backup_returns_descriptive_error_for_invalid_tag(tmp_path: Path, monkeypatch):
    service = RestoreService()
    encrypted_file, _ = _write_encrypted_backup(tmp_path, service, b"pg dump payload" * 64)
    service.storage = LocalBackupStorage(encrypted_file)

    def fake_decrypt_file(input_path: Path, output_path: Path, recovery_code: str | None = None) -> None:
        raise InvalidTag()

    monkeypatch.setattr(service.encryption, "decrypt_file", fake_decrypt_file)

    result = await service.restore_backup("broken.enc")

    assert result.success is False
    assert result.status == "decryption_failed"
    assert result.error == "Backup cannot be decrypted: wrong BACKUP_ENCRYPTION_KEY or corrupted file"


@pytest.mark.asyncio
async def test_restore_backup_requires_recovery_code_on_different_machine(tmp_path: Path):
    service = RestoreService()
    encrypted_file, _ = _write_encrypted_backup(tmp_path, service, b"pg dump payload" * 64)
    service.storage = LocalBackupStorage(encrypted_file)
    service.encryption = BackupEncryption("restore_suite_other_machine_master_key_456")

    result = await service.restore_backup("portable.enc")

    assert result.success is False
    assert result.status == "recovery_code_required"
    assert (
        result.error == "This portable backup was created on a different machine. Provide recovery code to restore it."
    )


@pytest.mark.asyncio
async def test_restore_backup_uses_recovery_code_on_different_machine(tmp_path: Path, monkeypatch):
    service = RestoreService()
    encrypted_file, recovery_code = _write_encrypted_backup(tmp_path, service, b"pg dump payload" * 64)
    service.storage = LocalBackupStorage(encrypted_file)
    service.encryption = BackupEncryption("restore_suite_other_machine_master_key_456")

    async def fake_pg_restore(dump_path: Path, target, drop_existing: bool) -> None:
        assert dump_path.exists()
        assert drop_existing is True

    monkeypatch.setattr(service, "_pg_restore", fake_pg_restore)

    result = await service.restore_backup("portable.enc", True, recovery_code)

    assert result.success is True
    assert result.status == "restored"
    assert result.offsite_used is False
    assert result.error is None


@pytest.mark.asyncio
async def test_restore_backup_rejects_invalid_recovery_code_on_different_machine(tmp_path: Path):
    service = RestoreService()
    encrypted_file, _ = _write_encrypted_backup(tmp_path, service, b"pg dump payload" * 64)
    service.storage = LocalBackupStorage(encrypted_file)
    service.encryption = BackupEncryption("restore_suite_other_machine_master_key_456")

    result = await service.restore_backup("portable.enc", True, "dead-beef-dead-beef")

    assert result.success is False
    assert result.status == "invalid_recovery_code"
    assert result.error == "Recovery code is invalid or backup is corrupted"


@pytest.mark.asyncio
async def test_verify_backup_requires_recovery_code_on_different_machine(tmp_path: Path):
    service = RestoreService()
    encrypted_file, _ = _write_encrypted_backup(tmp_path, service, b"pg dump payload" * 64)
    service.storage = LocalBackupStorage(encrypted_file)
    service.encryption = BackupEncryption("restore_suite_other_machine_master_key_456")

    result = await service.verify_backup("portable.enc")

    assert result.valid is False
    assert result.status == "recovery_code_required"
    assert (
        result.error == "This portable backup was created on a different machine. Provide recovery code to restore it."
    )


@pytest.mark.asyncio
async def test_verify_backup_uses_recovery_code_on_different_machine(tmp_path: Path, monkeypatch):
    service = RestoreService()
    encrypted_file, recovery_code = _write_encrypted_backup(tmp_path, service, b"pg dump payload" * 64)
    service.storage = LocalBackupStorage(encrypted_file)
    service.encryption = BackupEncryption("restore_suite_other_machine_master_key_456")

    async def fake_verify_dump(dump_path: Path) -> None:
        assert dump_path.exists()

    monkeypatch.setattr(service, "_verify_dump", fake_verify_dump)

    result = await service.verify_backup("portable.enc", recovery_code)

    assert result.valid is True
    assert result.status == "valid"
    assert result.error is None
