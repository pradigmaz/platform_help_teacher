"""
Tests for backup Telegram notifications.
"""

import os
from pathlib import Path

import pytest

os.environ.setdefault("BACKUP_ENCRYPTION_KEY", "test_backup_master_key_for_notification_suite_123")
os.environ.setdefault("MINIO_ROOT_USER", "test")
os.environ.setdefault("MINIO_ROOT_PASSWORD", "test")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")
os.environ.setdefault("TELEGRAM_WEBHOOK_SECRET", "test")

from app.services.backup.notification import BackupNotificationService, send_backup_to_admin_sync


class FakeBot:
    """Collects outgoing Telegram calls for assertions."""

    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    async def send_document(self, **kwargs):
        self.calls.append(("document", kwargs))

    async def send_message(self, **kwargs):
        self.calls.append(("message", kwargs))


@pytest.mark.asyncio
async def test_send_backup_to_admin_sends_recovery_code_separately(tmp_path: Path):
    file_path = tmp_path / "backup.enc"
    file_path.write_bytes(b"encrypted-backup")
    service = BackupNotificationService()
    service._bot = FakeBot()

    result = await service.send_backup_to_admin(
        file_path=file_path,
        backup_name="backup_20260312.enc",
        size=file_path.stat().st_size,
        recovery_code="abcd-1234-ef56-7890",
        admin_telegram_id=123456,
    )

    assert result.success is True
    assert result.error is None
    assert len(service._bot.calls) == 2

    document_call = service._bot.calls[0]
    assert document_call[0] == "document"
    assert "Второй код придет отдельным сообщением" in document_call[1]["caption"]

    message_call = service._bot.calls[1]
    assert message_call[0] == "message"
    assert "abcd-1234-ef56-7890" in message_call[1]["text"]
    assert "BACKUP_ENCRYPTION_KEY" in message_call[1]["text"]


def test_send_backup_to_admin_sync_sends_recovery_code_separately(tmp_path: Path, monkeypatch):
    file_path = tmp_path / "backup.enc"
    file_path.write_bytes(b"encrypted-backup")
    requests_calls: list[tuple[str, dict | None, dict | None]] = []

    class FakeResponse:
        def __init__(self, status_code: int = 200, text: str = "ok"):
            self.status_code = status_code
            self.text = text

    def fake_post(url, data=None, files=None, json=None, timeout=None):
        requests_calls.append((url, data or json, files))
        return FakeResponse()

    monkeypatch.setattr("requests.post", fake_post)

    result = send_backup_to_admin_sync(
        file_path=file_path,
        backup_name="backup_20260312.enc",
        size=file_path.stat().st_size,
        recovery_code="abcd-1234-ef56-7890",
        admin_telegram_id=123456,
    )

    assert result.success is True
    assert result.error is None
    assert len(requests_calls) == 2
    assert requests_calls[0][0].endswith("/sendDocument")
    assert "Второй код придет отдельным сообщением" in requests_calls[0][1]["caption"]
    assert requests_calls[1][0].endswith("/sendMessage")
    assert "abcd-1234-ef56-7890" in requests_calls[1][1]["text"]
