"""
Константы для Security Monitor.
"""
import re
from enum import Enum
from typing import NamedTuple, List, Pattern


class AttackType(str, Enum):
    """Типы атак."""
    SQL_INJECTION = "sql_injection"
    PATH_TRAVERSAL = "path_traversal"
    XSS = "xss"
    IDOR = "idor"  # Insecure Direct Object Reference
    HONEYPOT = "honeypot"  # Обращение к ловушке
    UNKNOWN = "unknown"


class StrikeLevel(str, Enum):
    """Уровни страйков."""
    NONE = "none"
    WARNING = "warning"      # 1-й страйк: только лог
    RECORDED = "recorded"    # 2-й страйк: запись в БД
    BANNED = "banned"        # 3-й страйк: бан


class AttackPattern(NamedTuple):
    """Паттерн атаки."""
    pattern: Pattern
    attack_type: AttackType
    description: str
    severity: int  # 1-3, влияет на скорость набора страйков


# Паттерны для детекции (компилируем заранее)
ATTACK_PATTERNS: List[AttackPattern] = [
    # SQL Injection
    AttackPattern(
        re.compile(r"['\"](\s*(OR|AND)\s*['\"]?\d|--|;)", re.IGNORECASE),
        AttackType.SQL_INJECTION,
        "SQL injection: OR/AND condition or comment",
        severity=3
    ),
    AttackPattern(
        re.compile(r"(UNION\s+(ALL\s+)?SELECT|INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM|DROP\s+TABLE)", re.IGNORECASE),
        AttackType.SQL_INJECTION,
        "SQL injection: dangerous statement",
        severity=3
    ),
    AttackPattern(
        re.compile(r"%27|%22|%3B|%2D%2D"),  # URL-encoded ', ", ;, --
        AttackType.SQL_INJECTION,
        "SQL injection: URL-encoded special chars",
        severity=2
    ),
    AttackPattern(
        re.compile(r"(\x00|%00)"),  # Null byte
        AttackType.SQL_INJECTION,
        "Null byte injection",
        severity=3
    ),
    
    # Path Traversal
    AttackPattern(
        re.compile(r"\.\.(/|\\|%2f|%5c)", re.IGNORECASE),
        AttackType.PATH_TRAVERSAL,
        "Path traversal attempt",
        severity=3
    ),
    AttackPattern(
        re.compile(r"%2e%2e(%2f|%5c)", re.IGNORECASE),
        AttackType.PATH_TRAVERSAL,
        "Path traversal: URL-encoded",
        severity=3
    ),
    
    # XSS
    AttackPattern(
        re.compile(r"<script[^>]*>|javascript:|on\w+\s*=", re.IGNORECASE),
        AttackType.XSS,
        "XSS: script injection",
        severity=2
    ),
]

# Redis ключи
REDIS_STRIKE_COUNT = "sec:strikes:{identifier}"
REDIS_STRIKE_DETAILS = "sec:strike_details:{identifier}"
REDIS_SECURITY_BAN = "sec:ban:{identifier}"

# Настройки
STRIKE_WINDOW = 3600  # 1 час — окно подсчёта страйков
BAN_DURATION = 3600   # 1 час — длительность бана
MAX_STRIKES = 3       # Страйков до бана

# Сообщения
MESSAGES = {
    StrikeLevel.WARNING: "⚠️ Обнаружена подозрительная активность. Это предупреждение.",
    StrikeLevel.RECORDED: "⚠️ Повторная подозрительная активность. Зафиксировано.",
    StrikeLevel.BANNED: "🚫 Доступ заблокирован на 1 час из-за подозрительной активности.",
}
