"""
Агрегатор роутеров для оценок и посещаемости журнала.
"""
from fastapi import APIRouter

from .attendance import router as attendance_router
from .grades_endpoints import router as grades_router
from .grades_bulk import router as grades_bulk_router

router = APIRouter()

# Подключаем все роутеры
router.include_router(attendance_router)
router.include_router(grades_router)
router.include_router(grades_bulk_router)
