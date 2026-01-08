"""
Утилиты для аудита: извлечение IP, санитизация.
"""
import json
import logging
from typing import Any, Dict, Optional, Set
from fastapi import Request

from .constants import SENSITIVE_FIELDS, MAX_BODY_SIZE, EXCLUDED_PATHS, AUDIT_PATH_PREFIXES
from .schemas import IPInfo

logger = logging.getLogger(__name__)


def extract_ip_info(request: Request) -> IPInfo:
    """
    Извлечь информацию об IP из запроса.
    Учитывает прокси (X-Forwarded-For, X-Real-IP).
    """
    client_ip = request.client.host if request.client else "unknown"
    
    # X-Forwarded-For: client, proxy1, proxy2
    forwarded_for = request.headers.get("X-Forwarded-For")
    x_real_ip = request.headers.get("X-Real-IP")
    
    real_ip = client_ip
    forwarded_chain = None
    is_proxy = False
    
    if forwarded_for:
        # Берём первый IP (оригинальный клиент)
        ips = [ip.strip() for ip in forwarded_for.split(",")]
        real_ip = ips[0]
        forwarded_chain = forwarded_for
        is_proxy = True
    elif x_real_ip:
        real_ip = x_real_ip
        is_proxy = True
    
    return IPInfo(
        real_ip=real_ip,
        forwarded_chain=forwarded_chain,
        is_proxy=is_proxy
    )


def sanitize_value(value: Any, field_name: str = "") -> Any:
    """Санитизация значения — маскировка sensitive данных."""
    field_lower = field_name.lower()
    
    # Проверяем sensitive fields
    for sensitive in SENSITIVE_FIELDS:
        if sensitive in field_lower:
            return "[REDACTED]"
    
    return value


def sanitize_dict(data: Dict[str, Any], max_depth: int = 3) -> Dict[str, Any]:
    """Рекурсивная санитизация словаря."""
    if max_depth <= 0:
        return {"_truncated": True}
    
    result = {}
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


async def extract_body(request: Request) -> Optional[Dict[str, Any]]:
    """Извлечь и санитизировать body запроса."""
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
                return sanitize_dict(data)
            return {"_raw": str(data)[:500]}
        except json.JSONDecodeError:
            # Не JSON — сохраняем как строку (обрезанную)
            return {"_raw": body.decode("utf-8", errors="ignore")[:500]}
    except Exception as e:
        logger.debug(f"Failed to extract body: {e}")
        return None


def should_audit(path: str) -> bool:
    """Проверить, нужно ли логировать этот путь."""
    # Исключения
    if path in EXCLUDED_PATHS:
        return False
    
    # Whitelist префиксов
    return any(path.startswith(prefix) for prefix in AUDIT_PATH_PREFIXES)


def extract_fingerprint(request: Request) -> Optional[Dict[str, Any]]:
    """Извлечь fingerprint из заголовков."""
    fp_header = request.headers.get("X-Device-Fingerprint")
    if not fp_header:
        return None
    
    try:
        return json.loads(fp_header)
    except json.JSONDecodeError:
        # Если не JSON — сохраняем как hash
        return {"hash": fp_header}
