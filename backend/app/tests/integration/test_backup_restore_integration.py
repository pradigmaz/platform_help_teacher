import gzip
import shutil
import sys
import types
from pathlib import Path

import pytest

if "aioboto3" not in sys.modules:
    aioboto3_stub = types.ModuleType("aioboto3")

    class Session:  # pragma: no cover - import-time compatibility only
        pass

    aioboto3_stub.Session = Session
    sys.modules["aioboto3"] = aioboto3_stub

from app.services.backup.dump_runner import PostgresConnectionConfig
from app.services.backup.restore_service import RestoreService

pytestmark = pytest.mark.integration


class LocalBackupStorage:
    def __init__(self, source_path: Path):
        self.source_path = source_path

    async def download(self, backup_key: str, local_path: Path) -> None:
        shutil.copyfile(self.source_path, local_path)


class FailingBackupStorage:
    async def download(self, backup_key: str, local_path: Path) -> None:
        raise FileNotFoundError(f"missing {backup_key}")


def write_encrypted_backup(tmp_path: Path, service: RestoreService, dump_bytes: bytes) -> Path:
    compressed_file = tmp_path / "backup.dump.gz"
    encrypted_file = tmp_path / "backup.enc"
    compressed_file.write_bytes(gzip.compress(dump_bytes))
    service.encryption.encrypt_file(compressed_file, encrypted_file)
    return encrypted_file


@pytest.mark.asyncio
async def test_verify_backup_roundtrip_uses_real_archive_pipeline(tmp_path: Path, monkeypatch):
    service = RestoreService()
    encrypted_file = write_encrypted_backup(tmp_path, service, b"pg dump payload" * 64)
    service.storage = LocalBackupStorage(encrypted_file)

    async def fake_verify_dump(dump_path: Path) -> None:
        assert dump_path.exists()
        assert dump_path.read_bytes().startswith(b"pg dump payload")

    monkeypatch.setattr(service, "_verify_dump", fake_verify_dump)

    result = await service.verify_backup("integration.enc")

    assert result.valid is True
    assert result.status == "valid"
    assert result.error is None
    assert result.offsite_used is False
    assert result.format_version == 3


@pytest.mark.asyncio
async def test_restore_backup_uses_offsite_fallback_and_real_decrypt_pipeline(tmp_path: Path, monkeypatch):
    service = RestoreService()
    encrypted_file = write_encrypted_backup(tmp_path, service, b"pg dump payload" * 64)
    service.storage = FailingBackupStorage()
    service.offsite_storage = LocalBackupStorage(encrypted_file)

    observed = {}

    async def fake_pg_restore(
        dump_path: Path,
        target: PostgresConnectionConfig,
        drop_existing: bool,
    ) -> None:
        observed["dump_exists"] = dump_path.exists()
        observed["dump_prefix"] = dump_path.read_bytes()[:16]
        observed["target_host"] = target.host
        observed["drop_existing"] = drop_existing

    monkeypatch.setattr(service, "_pg_restore", fake_pg_restore)

    result = await service.restore_backup_to_target(
        "integration.enc",
        target=PostgresConnectionConfig(
            host="restore-host",
            port=5432,
            user="restore-user",
            password="restore-password",
            dbname="restore-db",
        ),
        drop_existing=True,
    )

    assert result.success is True
    assert result.status == "restored"
    assert result.error is None
    assert result.offsite_used is True
    assert observed == {
        "dump_exists": True,
        "dump_prefix": b"pg dump payloadp",
        "target_host": "restore-host",
        "drop_existing": True,
    }
