"""
Централизованная генерация кодов.

Все коды в системе должны генерироваться через этот модуль
для обеспечения единообразия и безопасности.
"""

import secrets
import string

# Алфавиты для разных типов кодов
ALPHANUMERIC_UPPER = string.ascii_uppercase + string.digits  # A-Z, 0-9
ALPHANUMERIC_SAFE = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # Без O/0, I/1/l
DIGITS_ONLY = string.digits  # 0-9
ALPHANUMERIC_LOWER = string.ascii_lowercase + string.digits  # a-z, 0-9


def generate_code(
    length: int,
    alphabet: str = ALPHANUMERIC_SAFE,
) -> str:
    """
    Генерирует криптографически безопасный код.

    Args:
        length: Длина кода
        alphabet: Алфавит символов

    Returns:
        Сгенерированный код
    """
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_otp(length: int = 6) -> str:
    """Генерирует OTP код (только цифры)."""
    return generate_code(length, DIGITS_ONLY)


def generate_invite_code(length: int = 8) -> str:
    """Генерирует инвайт-код (безопасный алфавит без похожих символов)."""
    return generate_code(length, ALPHANUMERIC_SAFE)


def generate_relink_code(length: int = 6) -> str:
    """Генерирует relink-код (A-Z, 0-9)."""
    return generate_code(length, ALPHANUMERIC_UPPER)


def generate_public_code(length: int = 8) -> str:
    """Генерирует публичный код для ссылок (a-z, 0-9)."""
    return generate_code(length, ALPHANUMERIC_LOWER)


def generate_report_code(length: int = 8) -> str:
    """Генерирует код отчёта (безопасный алфавит)."""
    return generate_code(length, ALPHANUMERIC_SAFE)


def mask_code(code: str, visible_chars: int = 2) -> str:
    """
    Маскирует код для логирования.

    Args:
        code: Исходный код
        visible_chars: Количество видимых символов в начале

    Returns:
        Замаскированный код (например: "AB***")
    """
    if len(code) <= visible_chars:
        return "*" * len(code)
    return code[:visible_chars] + "***"
