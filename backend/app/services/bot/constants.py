"""Константы и типы для бот-сервисов."""
import re
from typing import Literal

from app.core.config import settings
from app.core.time_constants import (
    CODE_ATTEMPTS_WINDOW_SECONDS,
    FSM_TTL_SECONDS,
    OTP_TTL_SECONDS,
    RELINK_TTL_SECONDS,
)
from app.core.time_constants import (
    CODE_LOCKOUT_SECONDS as CODE_LOCKOUT_TIME,
)

Platform = Literal["telegram", "vk"]

# TTL для временных данных
RELINK_TTL = RELINK_TTL_SECONDS
FSM_TTL = FSM_TTL_SECONDS
OTP_TTL = OTP_TTL_SECONDS

# Rate limiting для команды /code
MAX_CODE_ATTEMPTS = settings.MAX_PIN_ATTEMPTS
CODE_LOCKOUT_SECONDS = CODE_LOCKOUT_TIME
CODE_ATTEMPTS_WINDOW = CODE_ATTEMPTS_WINDOW_SECONDS

# Паттерн валидации кодов (6-8 символов, A-Z и 0-9)
CODE_PATTERN = re.compile(r'^[A-Z0-9]{6,8}$')

# Минимальное время ответа для защиты от timing attack
MIN_RESPONSE_TIME = 0.1  # 100ms
