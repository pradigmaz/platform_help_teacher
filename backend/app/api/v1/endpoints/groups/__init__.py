"""Groups API module."""
from fastapi import APIRouter

from .crud import router as crud_router
from .students import router as students_router
from .subgroups import router as subgroups_router
from .settings import router as settings_router

router = APIRouter()

# Include all sub-routers
router.include_router(crud_router)
router.include_router(students_router)
router.include_router(subgroups_router)
router.include_router(settings_router)
