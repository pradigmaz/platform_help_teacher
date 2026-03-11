from fastapi import Request
from slowapi import Limiter

from app.core.client_ip import extract_client_ip


def get_rate_limit_ip(request: Request) -> str:
    client_ip = extract_client_ip(request)
    return client_ip.value or "unknown"


# Используем IP адрес клиента для идентификации
# default_limits — fallback для эндпоинтов без явного @limiter.limit()
limiter = Limiter(
    key_func=get_rate_limit_ip,
    default_limits=["10000/minute", "100000/hour"],  # Dev: высокие лимиты
)
