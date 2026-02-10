"""
Константы для Security Monitor.
"""
import re
from enum import Enum
from re import Pattern
from typing import NamedTuple

from app.core.time_constants import (
    BAN_DURATION_SECONDS,
    STRIKE_WINDOW_SECONDS,
)
from app.core.time_constants import (
    MAX_STRIKES as MAX_STRIKES_LIMIT,
)


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
# ВАЖНО: severity снижен, чтобы избежать мгновенных банов за false positives
# severity=1: предупреждение, severity=2: 2 страйка, severity=3: мгновенный бан
ATTACK_PATTERNS: list[AttackPattern] = [
    # SQL Injection — только явные атаки
    # УБРАНО: r"['\"](\s*(OR|AND)\s*['\"]?\d|--|;)" — слишком много false positives
    # Срабатывал на легитимные запросы с кавычками в тексте
    AttackPattern(
        re.compile(r"(UNION\s+(ALL\s+)?SELECT|INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM|DROP\s+TABLE)", re.IGNORECASE),
        AttackType.SQL_INJECTION,
        "SQL injection: dangerous statement",
        severity=2  # Было 3 — снижено, чтобы не банить сразу
    ),
    # УБРАНО: r"%27|%22|%3B|%2D%2D" — URL-encoded кавычки встречаются в легитимных запросах
    # Поиск текста, названия с кавычками, JSON в query params
    AttackPattern(
        re.compile(r"(\x00|%00)"),  # Null byte — это точно атака
        AttackType.SQL_INJECTION,
        "Null byte injection",
        severity=2  # Было 3
    ),

    # Path Traversal
    AttackPattern(
        re.compile(r"\.\.(/|\\|%2f|%5c)", re.IGNORECASE),
        AttackType.PATH_TRAVERSAL,
        "Path traversal attempt",
        severity=2  # Было 3
    ),
    AttackPattern(
        re.compile(r"%2e%2e(%2f|%5c)", re.IGNORECASE),
        AttackType.PATH_TRAVERSAL,
        "Path traversal: URL-encoded",
        severity=2  # Было 3
    ),

    # XSS
    AttackPattern(
        re.compile(r"<script[^>]*>|javascript:", re.IGNORECASE),
        AttackType.XSS,
        "XSS: script tag or javascript protocol",
        severity=2
    ),
    # XSS event handlers — только в контексте HTML-тегов
    AttackPattern(
        re.compile(r"<[^>]+\s+on(click|load|error|mouse\w+|key\w+|focus|blur|change|submit)\s*=", re.IGNORECASE),
        AttackType.XSS,
        "XSS: event handler in HTML tag",
        severity=2
    ),
]

# Redis ключи
REDIS_STRIKE_COUNT = "sec:strikes:{identifier}"
REDIS_STRIKE_DETAILS = "sec:strike_details:{identifier}"
REDIS_SECURITY_BAN = "sec:ban:{identifier}"

# Настройки
STRIKE_WINDOW = STRIKE_WINDOW_SECONDS
BAN_DURATION = BAN_DURATION_SECONDS
MAX_STRIKES = MAX_STRIKES_LIMIT

# Сообщения (ASCII для HTTP headers, русские для JSON body)
MESSAGES = {
    StrikeLevel.WARNING: "Suspicious activity detected. Warning.",
    StrikeLevel.RECORDED: "Repeated suspicious activity. Recorded.",
    StrikeLevel.BANNED: "Access blocked for 1 hour.",
}

MESSAGES_RU = {
    StrikeLevel.WARNING: "⚠️ Обнаружена подозрительная активность. Это предупреждение.",
    StrikeLevel.RECORDED: "⚠️ Повторная подозрительная активность. Зафиксировано.",
    StrikeLevel.BANNED: "🚫 Посиди в бане за плохое поведение. Доступ заблокирован на 1 час.",
}
