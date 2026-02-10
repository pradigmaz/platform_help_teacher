"""Реэкспорт из модуля attestation/."""
from app.services.attestation import (
    AttendanceScoreResult,
    AttestationCalculator,
    AttestationService,
    LabScoreResult,
)

__all__ = [
    "AttestationService",
    "AttestationCalculator",
    "LabScoreResult",
    "AttendanceScoreResult",
]
