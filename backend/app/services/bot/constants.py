"""Константы и типы для бот-сервисов."""
import re
from typing import Literal

from app.core.config import settings

Platform = Literal["telegram", "vk"]

# TTL для временных данных (из config для гибкости)
RELINK_TTL = 300  # 5 минут
FSM_TTL = 600  # 10 минут для FSM состояния
OTP_TTL = 300  # 5 минут

# Rate limiting для команды /code
MAX_CODE_ATTEMPTS = settings.MAX_PIN_ATTEMPTS  # Используем общую настройку
CODE_LOCKOUT_SECONDS = 900  # 15 минут
CODE_ATTEMPTS_WINDOW = 3600  # 1 час

# Паттерн валидации кодов (6-8 символов, A-Z и 0-9)
CODE_PATTERN = re.compile(r'^[A-Z0-9]{6,8}$')

# Минимальное время ответа для защиты от timing attack
MIN_RESPONSE_TIME = 0.1  # 100ms
