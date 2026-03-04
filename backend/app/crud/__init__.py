"""
CRUD операции для моделей приложения.
"""

from app.crud.attendance import (
    AttendanceValidationError,
    DuplicateAttendanceError,
    FutureDateError,
    StudentNotFoundError,
    StudentNotInGroupError,
    bulk_create_attendance,
    check_attendance_exists,
    create_attendance,
    delete_attendance,
    get_attendance_by_group_and_date,
    get_attendance_by_group_date_range,
    get_attendance_by_student,
    update_attendance,
    upsert_attendance,
    validate_student_in_group,
)
from app.crud.crud_subject import (
    assign_teacher_to_subject,
    create_subject,
    get_all_subjects,
    get_or_create_assignment_from_schedule,
    get_or_create_subject,
    get_subject,
    get_subject_by_name,
    get_subject_teachers,
    get_teacher_subjects,
)
from app.crud.crud_user import get_by_social_id, upsert_user
from app.crud import crud_device
from app.crud.report import crud_report

__all__ = [
    # User CRUD
    "get_by_social_id",
    "upsert_user",
    # Attendance CRUD
    "create_attendance",
    "update_attendance",
    "upsert_attendance",
    "get_attendance_by_student",
    "get_attendance_by_group_and_date",
    "get_attendance_by_group_date_range",
    "delete_attendance",
    "bulk_create_attendance",
    "validate_student_in_group",
    "check_attendance_exists",
    # Exceptions
    "AttendanceValidationError",
    "DuplicateAttendanceError",
    "StudentNotInGroupError",
    "StudentNotFoundError",
    "FutureDateError",
    # Subject CRUD
    "get_subject",
    "get_subject_by_name",
    "get_all_subjects",
    "create_subject",
    "get_or_create_subject",
    "get_teacher_subjects",
    "get_subject_teachers",
    "assign_teacher_to_subject",
    "get_or_create_assignment_from_schedule",
    # Device CRUD
    "crud_device",
    # Report CRUD
    "crud_report",
]
