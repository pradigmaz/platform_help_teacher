"""Backward-compatible aliases for the canonical attendance write service."""

from app.services.journal_attendance_service import (
    JournalAttendanceService as JournalAttendanceWriteService,
)
from app.services.journal_attendance_service import (
    JournalAttendanceValidationError as AttendanceWriteValidationError,
)
from app.services.journal_attendance_service import (
    journal_attendance_service as journal_attendance_write_service,
)

__all__ = [
    "AttendanceWriteValidationError",
    "JournalAttendanceWriteService",
    "journal_attendance_write_service",
]
