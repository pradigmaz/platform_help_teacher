"""Реэкспорт из модуля attestation/."""
from app.services.attestation import (
    AttestationService,
    AttestationCalculator,
    LabScoreResult,
    AttendanceScoreResult,
)

__all__ = [
    "AttestationService",
    "AttestationCalculator",
    "LabScoreResult",
    "AttendanceScoreResult",
]
