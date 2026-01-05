from slowapi import Limiter
from slowapi.util import get_remote_address

# Используем IP адрес клиента для идентификации
limiter = Limiter(key_func=get_remote_address)