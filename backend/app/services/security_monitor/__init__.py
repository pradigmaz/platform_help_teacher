"""
Security Monitor — детекция и блокировка подозрительных запросов.

Система "3 страйка":
1. WARNING — логируем, header в ответе
2. RECORDED — фиксируем в БД
3. BAN — блокировка на 1 час
"""
from .detector import SecurityDetector, get_security_detector
from .constants import AttackType, StrikeLevel, ATTACK_PATTERNS

__all__ = [
    "SecurityDetector",
    "get_security_detector", 
    "AttackType",
    "StrikeLevel",
    "ATTACK_PATTERNS",
]
