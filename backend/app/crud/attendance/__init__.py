"""Attendance CRUD operations."""
from .crud import (
    bulk_create_attendance,
    create_attendance,
    delete_attendance,
    update_attendance,
    upsert_attendance,
)
from .exceptions import (
    AttendanceValidationError,
    DuplicateAttendanceError,
    FutureDateError,
    StudentNotFoundError,
    StudentNotInGroupError,
)
from .queries import (
    check_attendance_exists,
    get_attendance_by_group_and_date,
    get_attendance_by_group_date_range,
    get_attendance_by_student,
)
from .validators import validate_student_in_group

__all__ = [
    # Exceptions
    "AttendanceValidationError",
    "DuplicateAttendanceError",
    "StudentNotInGroupError",
    "StudentNotFoundError",
    "FutureDateError",
    # CRUD
    "create_attendance",
    "update_attendance",
    "upsert_attendance",
    "delete_attendance",
    "bulk_create_attendance",
    # Queries
    "get_attendance_by_student",
    "get_attendance_by_group_and_date",
    "get_attendance_by_group_date_range",
    "check_attendance_exists",
    # Validators
    "validate_student_in_group",
]
