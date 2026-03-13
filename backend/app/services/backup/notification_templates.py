"""Message builders for backup notifications."""


def build_backup_caption(backup_name: str, size_kb: float) -> str:
    """Build Telegram/VK caption for the encrypted backup artifact."""
    return (
        f"🔐 <b>Резервная копия БД</b>\n\n"
        f"📦 <code>{backup_name}</code>\n"
        f"📊 Размер: {size_kb:.1f} KB\n\n"
        "⚠️ Файл зашифрован AES-256-GCM\n"
        "🧩 Второй код придет отдельным сообщением"
    )


def build_recovery_code_message(backup_name: str, recovery_code: str) -> str:
    """Build separate Telegram message for portable recovery."""
    return (
        "Шаг 2/2 для переноса на другую машину\n\n"
        f"📦 <code>{backup_name}</code>\n"
        f"🧩 <code>{recovery_code}</code>\n\n"
        "Это одноразовый код именно для этого backup.\n"
        "Не путать с BACKUP_ENCRYPTION_KEY."
    )
