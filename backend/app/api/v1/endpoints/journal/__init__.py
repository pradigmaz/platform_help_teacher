"""
Модуль журнала - эндпоинты для занятий, посещаемости и оценок.
"""
from .export import router as export_router
from .grades import router as grades_router
from .lessons import router as lessons_router

__all__ = ["lessons_router", "grades_router", "export_router"]
