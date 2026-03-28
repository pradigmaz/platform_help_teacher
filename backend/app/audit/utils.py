"""
Утилиты для аудита: извлечение IP, санитизация.
"""

import json
import logging
from typing import Any

from fastapi import Request

from app.fingerprint_contract import build_compact_audit_fingerprint

from .constants import (
    ALLOWED_BODY_FIELDS,
    AUDIT_EXACT_PATHS,
    AUDIT_PATH_PREFIXES,
    EXCLUDED_PATHS,
    MAX_BODY_SIZE,
    MAX_QUERY_PARAM_ITEMS,
    MAX_QUERY_PARAMS_SIZE,
    MAX_QUERY_VALUE_LENGTH,
    SENSITIVE_FIELDS,
)
from .schemas import IPInfo

logger = logging.getLogger(__name__)


def extract_ip_info(request: Request) -> IPInfo:
    """
    Извлечь информацию об IP из запроса.

    Приоритет:
    1. X-Real-IP (устанавливается nginx для реального IP клиента)
    2. client.host (fallback)

    X-Forwarded-For сохраняется для forensics, но НЕ используется
    для определения real_ip (может быть подделан клиентом).
    """
    client_ip = request.client.host if request.client else "unknown"

    # X-Real-IP устанавливается trusted proxy (nginx)
    x_real_ip = request.headers.get("X-Real-IP")

    # X-Forwarded-For сохраняем для информации, но не доверяем
    forwarded_for = request.headers.get("X-Forwarded-For")

    # Определяем реальный IP
    if x_real_ip:
        real_ip = x_real_ip.strip()
        is_proxy = True
    else:
        real_ip = client_ip
        is_proxy = False

    # Валидация формата IP (базовая)
    if not _is_valid_ip(real_ip):
        real_ip = client_ip

    return IPInfo(real_ip=real_ip, forwarded_chain=forwarded_for, is_proxy=is_proxy)


def _is_valid_ip(ip: str) -> bool:
    """Базовая валидация формата IP адреса."""
    if not ip or ip == "unknown":
        return False
    # IPv4 или IPv6
    parts = ip.split(".")
    if len(parts) == 4:
        return all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)
    # IPv6 - просто проверяем наличие :
    return ":" in ip


def sanitize_value(value: Any, field_name: str = "") -> Any:
    """Санитизация значения — маскировка sensitive данных."""
    field_lower = field_name.lower()

    # Проверяем sensitive fields
    for sensitive in SENSITIVE_FIELDS:
        if sensitive in field_lower:
            return "[REDACTED]"

    return value


def sanitize_dict(data: dict[str, Any], max_depth: int = 3) -> dict[str, Any]:
    """Рекурсивная санитизация словаря."""
    if max_depth <= 0:
        return {"_truncated": True}

    result: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = sanitize_dict(value, max_depth - 1)
        elif isinstance(value, list):
            result[key] = [
                sanitize_dict(v, max_depth - 1) if isinstance(v, dict) else sanitize_value(v, key)
                for v in value[:10]  # Лимит на элементы списка
            ]
        else:
            result[key] = sanitize_value(value, key)

    return result


def _truncate_string(value: str, max_length: int) -> str:
    """Ограничить длину строки для компактного хранения."""
    if len(value) <= max_length:
        return value
    return value[:max_length] + "...[TRUNCATED]"


async def extract_body(request: Request) -> dict[str, Any] | None:
    """
    Извлечь и санитизировать body запроса.

    Security: сохраняем только whitelist полей, остальные отфильтровываются.
    PII protection: не сохраняем персональные данные.
    """
    if request.method not in ("POST", "PUT", "PATCH"):
        return None

    try:
        # Проверяем размер
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY_SIZE:
            return {"_truncated": True, "_size": content_length}

        body = await request.body()
        if not body:
            return None

        # Пробуем распарсить JSON
        try:
            data = json.loads(body)
            if isinstance(data, dict):
                # Фильтруем только разрешённые поля
                filtered = {}
                for key in ALLOWED_BODY_FIELDS:
                    if key in data:
                        filtered[key] = sanitize_value(data[key], key)
                return filtered if filtered else None
            return None  # Не сохраняем non-dict body
        except json.JSONDecodeError:
            return None  # Не сохраняем non-JSON body
    except Exception as e:
        logger.debug(f"Failed to extract body: {e}")
        return None


def extract_query_params(request: Request) -> dict[str, Any] | None:
    """
    Извлечь query params в компактном и безопасном виде.

    Не сохраняем длинные query strings целиком, чтобы не раздувать audit.
    """
    if not request.query_params:
        return None

    params = dict(request.query_params)
    if not params:
        return None

    compact_params: dict[str, Any] = {}
    total_items = len(params)

    for index, (key, value) in enumerate(params.items()):
        if index >= MAX_QUERY_PARAM_ITEMS:
            compact_params["_truncated"] = True
            compact_params["_items"] = total_items
            break

        sanitized = sanitize_value(value, key)
        if isinstance(sanitized, str):
            sanitized = _truncate_string(sanitized, MAX_QUERY_VALUE_LENGTH)
        compact_params[key] = sanitized

    try:
        payload_size = len(json.dumps(compact_params, ensure_ascii=True).encode("utf-8"))
    except (TypeError, ValueError):
        logger.debug("Failed to serialize compact query params")
        return {"_truncated": True, "_items": total_items}

    if payload_size > MAX_QUERY_PARAMS_SIZE:
        return {
            "_truncated": True,
            "_items": total_items,
            "_size": payload_size,
        }

    return compact_params or None


def should_audit(path: str) -> bool:
    """Проверить, нужно ли логировать этот путь."""
    # Исключения
    if path in EXCLUDED_PATHS:
        return False

    if path in AUDIT_EXACT_PATHS:
        return True

    # Whitelist префиксов
    return any(path.startswith(prefix) for prefix in AUDIT_PATH_PREFIXES)


def extract_fingerprint(request: Request) -> dict[str, Any] | None:
    """Извлечь fingerprint из заголовков."""
    return build_compact_audit_fingerprint(request.headers.get("X-Device-Fingerprint"))
