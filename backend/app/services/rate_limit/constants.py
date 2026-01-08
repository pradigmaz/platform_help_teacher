"""
Константы для системы rate limit предупреждений.
"""
from enum import Enum
from typing import NamedTuple


class WarningLevel(str, Enum):
    """Уровни предупреждений."""
    NONE = "none"
    SOFT_WARNING = "soft_warning"      # Просто header в ответе
    RECORDED_WARNING = "recorded"       # Записано в БД
    SOFT_BAN = "soft_ban"              # Временный бан 10 мин
    HARD_BAN = "hard_ban"              # Бан 1 час


class Threshold(NamedTuple):
    """Порог для уровня предупреждения."""
    count: int
    level: WarningLevel
    ban_duration: int  # секунды, 0 = нет бана
    notify_admin: bool


# Пороги (429 ошибок за COUNT_WINDOW)
THRESHOLDS = [
    Threshold(count=10, level=WarningLevel.SOFT_WARNING, ban_duration=0, notify_admin=False),
    Threshold(count=30, level=WarningLevel.RECORDED_WARNING, ban_duration=0, notify_admin=False),
    Threshold(count=50, level=WarningLevel.SOFT_BAN, ban_duration=600, notify_admin=True),  # 10 мин
    Threshold(count=100, level=WarningLevel.HARD_BAN, ban_duration=3600, notify_admin=True),  # 1 час
]

# Окно подсчёта 429 ошибок
COUNT_WINDOW = 300  # 5 минут

# Redis ключи
REDIS_429_COUNT = "rl:429:{identifier}"
REDIS_BAN = "rl:ban:{identifier}"
REDIS_WARNING_SENT = "rl:warn_sent:{identifier}"

# Сообщения
MESSAGES = {
    WarningLevel.SOFT_WARNING: "Вы отправляете слишком много запросов. Пожалуйста, подождите.",
    WarningLevel.RECORDED_WARNING: "Предупреждение: превышен лимит запросов. Это зафиксировано.",
    WarningLevel.SOFT_BAN: "Временная блокировка на 10 минут из-за превышения лимита запросов.",
    WarningLevel.HARD_BAN: "Блокировка на 1 час. Обратитесь к преподавателю для разблокировки.",
}
