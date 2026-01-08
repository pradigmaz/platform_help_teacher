"""Admin attestation API endpoints."""
from fastapi import APIRouter

from .settings import router as settings_router
from .calculation import router as calculation_router
from .audit import router as audit_router

router = APIRouter()

router.include_router(settings_router, tags=["attestation-settings"])
router.include_router(calculation_router, tags=["attestation-calculation"])
router.include_router(audit_router, tags=["attestation-audit"])
