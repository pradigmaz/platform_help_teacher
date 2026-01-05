"""
Обратная совместимость - реэкспорт из нового модуля attestation/.

Используйте:
    from app.services.attestation import AttestationService, AttestationCalculator
"""
from app.services.attestation import (
    AttestationService,
    AttestationCalculator,
    LabScoreResult,
    AttendanceScoreResult,
    WorkScoreResult,
)

__all__ = [
    "AttestationService",
    "AttestationCalculator",
    "LabScoreResult",
    "AttendanceScoreResult",
    "WorkScoreResult",
]
