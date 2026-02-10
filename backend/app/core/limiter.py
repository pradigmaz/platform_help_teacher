from slowapi import Limiter
from slowapi.util import get_remote_address

# Используем IP адрес клиента для идентификации
# default_limits — fallback для эндпоинтов без явного @limiter.limit()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["10000/minute", "100000/hour"],  # Dev: высокие лимиты
)
