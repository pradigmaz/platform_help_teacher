"""
Модуль журнала - эндпоинты для занятий, посещаемости и оценок.
"""
from .lessons import router as lessons_router
from .grades import router as grades_router

__all__ = ["lessons_router", "grades_router"]
