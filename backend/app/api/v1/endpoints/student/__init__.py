"""
Student API endpoints - личный кабинет студента.
"""
from fastapi import APIRouter

from .profile import router as profile_router
from .attendance import router as attendance_router
from .labs import router as labs_router
from .attestation import router as attestation_router
from .misc import router as misc_router

router = APIRouter()

router.include_router(profile_router, tags=["student-profile"])
router.include_router(attendance_router, tags=["student-attendance"])
router.include_router(labs_router, tags=["student-labs"])
router.include_router(attestation_router, tags=["student-attestation"])
router.include_router(misc_router, tags=["student-misc"])
