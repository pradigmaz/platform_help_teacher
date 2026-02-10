"""
API endpoints для журнала посещаемости и оценок.
Фасад - объединяет роутеры из journal/
"""
from fastapi import APIRouter

from .journal.export import router as export_router
from .journal.grades import router as grades_router
from .journal.lessons import router as lessons_router

router = APIRouter()

# Include sub-routers
router.include_router(lessons_router, tags=["journal-lessons"])
router.include_router(grades_router, tags=["journal-grades"])
router.include_router(export_router, tags=["journal-export"])
