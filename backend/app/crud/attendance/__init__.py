"""Attendance CRUD operations."""
from .exceptions import (
    AttendanceValidationError,
    DuplicateAttendanceError,
    StudentNotInGroupError,
    StudentNotFoundError,
    FutureDateError,
)
from .crud import (
    create_attendance,
    update_attendance,
    upsert_attendance,
    delete_attendance,
    bulk_create_attendance,
)
from .queries import (
    get_attendance_by_student,
    get_attendance_by_group_and_date,
    get_attendance_by_group_date_range,
    check_attendance_exists,
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
