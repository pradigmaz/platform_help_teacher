"""
Admin backup API - modular structure.
"""
from fastapi import APIRouter

from .crud import router as crud_router
from .restore import router as restore_router
from .settings import router as settings_router

router = APIRouter()

# Include all sub-routers
router.include_router(crud_router)
router.include_router(restore_router)
router.include_router(settings_router)
