"""
Модуль публичных отчётов.

Структура:
- service.py: Основной сервис (фасад)
- security.py: Генерация кодов, работа с PIN
- audit.py: Логирование просмотров
- data_collector.py: Сбор данных для отчётов
"""

from .audit import ReportAuditService
from .data_collector import ReportDataCollector
from .security import generate_code, hash_pin, verify_pin
from .service import ReportService

__all__ = [
    "ReportService",
    "ReportAuditService",
    "ReportDataCollector",
    "generate_code",
    "hash_pin",
    "verify_pin",
]
