"""Backward-compatible aliases for the canonical grade write service."""

from app.services.journal_grade_service import (
    JournalGradeConflictError as GradeWriteConflictError,
)
from app.services.journal_grade_service import (
    JournalGradeValidationError as GradeWriteValidationError,
)
from app.services.journal_grade_service import (
    JournalGradeWriteService,
)
from app.services.journal_grade_service import (
    journal_grade_service as journal_grade_write_service,
)

__all__ = [
    "GradeWriteConflictError",
    "GradeWriteValidationError",
    "JournalGradeWriteService",
    "journal_grade_write_service",
]
