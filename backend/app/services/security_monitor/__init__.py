"""
Security Monitor — детекция и блокировка подозрительных запросов.

Система "3 страйка":
1. WARNING — логируем, header в ответе
2. RECORDED — фиксируем в БД
3. BAN — блокировка на 1 час
"""

from .constants import ATTACK_PATTERNS, AttackType, StrikeLevel
from .detector import SecurityDetector, get_security_detector

__all__ = [
    "SecurityDetector",
    "get_security_detector",
    "AttackType",
    "StrikeLevel",
    "ATTACK_PATTERNS",
]
