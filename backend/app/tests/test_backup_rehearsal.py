"""
Tests for backup rehearsal CLI.
"""

import json
import os

os.environ.setdefault("BACKUP_ENCRYPTION_KEY", "test_backup_master_key_for_rehearsal_suite_123")
os.environ.setdefault("MINIO_ROOT_USER", "test")
os.environ.setdefault("MINIO_ROOT_PASSWORD", "test")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")
os.environ.setdefault("TELEGRAM_WEBHOOK_SECRET", "test")

from app.scripts import backup_rehearsal
from app.services.backup.results import RestoreResult


def test_restore_smoke_cli_returns_success(monkeypatch, capsys):
    async def fake_restore(self, backup_key, *, target, drop_existing=False, recovery_code=None):
        assert backup_key == "backup.enc"
        assert target.host == "smoke-db"
        assert target.port == 5433
        assert target.dbname == "smoke_db"
        assert target.user == "smoke_user"
        assert target.password == "smoke_password"
        assert drop_existing is True
        assert recovery_code == "abcd-1234"
        return RestoreResult(success=True, status="restored", offsite_used=False, format_version=3, portable=True)

    monkeypatch.setattr("app.services.backup.restore_service.RestoreService.restore_backup_to_target", fake_restore)

    exit_code = backup_rehearsal.main(
        [
            "restore-smoke",
            "--backup-key",
            "backup.enc",
            "--target-db-host",
            "smoke-db",
            "--target-db-port",
            "5433",
            "--target-db-name",
            "smoke_db",
            "--target-db-user",
            "smoke_user",
            "--target-db-password",
            "smoke_password",
            "--recovery-code",
            "abcd-1234",
            "--drop-existing",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["success"] is True
    assert payload["status"] == "restored"


def test_restore_smoke_cli_returns_failure(monkeypatch, capsys):
    async def fake_restore(self, backup_key, *, target, drop_existing=False, recovery_code=None):
        return RestoreResult(success=False, status="dump_invalid", error="pg_restore failed")

    monkeypatch.setattr("app.services.backup.restore_service.RestoreService.restore_backup_to_target", fake_restore)

    exit_code = backup_rehearsal.main(
        [
            "restore-smoke",
            "--backup-key",
            "broken.enc",
            "--target-db-host",
            "smoke-db",
            "--target-db-name",
            "smoke_db",
            "--target-db-user",
            "smoke_user",
            "--target-db-password",
            "smoke_password",
        ]
    )

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["success"] is False
    assert payload["error"] == "pg_restore failed"
