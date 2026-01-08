"""
Admin backup API - modular structure.
"""
from fastapi import APIRouter

from .crud import router as crud_router
from .restore import router as restore_router
from .settings import router as settings_router

router = APIRouter()

# Include all sub-routers (no prefix needed - main router has /admin/backups)
router.include_router(crud_router, tags=["backup_crud"])
router.include_router(restore_router, tags=["backup_restore"])
router.include_router(settings_router, tags=["backup_settings"])
