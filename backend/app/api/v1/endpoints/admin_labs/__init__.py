"""Admin labs API endpoints."""
from fastapi import APIRouter

from .labs_crud import router as labs_crud_router
from .lab_settings import router as lab_settings_router
from .deadline_extensions import router as deadline_extensions_router

router = APIRouter()

router.include_router(labs_crud_router, tags=["admin_labs"])
router.include_router(lab_settings_router, tags=["admin_lab_settings"])
router.include_router(deadline_extensions_router, tags=["admin_deadline_extensions"])
