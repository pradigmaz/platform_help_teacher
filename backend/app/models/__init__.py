# SQLAlchemy models
from .base import Base, TimestampMixin
from .user import User, UserRole
from .lecture_group import LectureGroup  # Must be before Group and Lecture
from .group import Group
from .lecture import Lecture
from .lecture_image import LectureImage
from .lab import Lab
from .submission import Submission, SubmissionStatus
from .lab_settings import LabSettings, GradingScale
from .attestation_settings import AttestationSettings, AttestationType
from .activity import Activity
from .attendance import Attendance, AttendanceStatus
from .work_type import WorkType
from .work import Work
from .work_submission import WorkSubmission
from .schedule import ScheduleItem, DayOfWeek, LessonType, WeekParity
from .lesson import Lesson
from .lesson_grade import LessonGrade
from .subject import Subject
from .teacher_subject import TeacherSubjectAssignment
from .schedule_parser_config import ScheduleParserConfig
from .schedule_conflict import ScheduleConflict, ConflictType
from .parse_history import ParseHistory
from .note import Note, EntityType as NoteEntityType, NoteColor
from .group_report import GroupReport, ReportType
from .report_view import ReportView
from .student_transfer import StudentTransfer
from .settings_audit import SettingsAuditLog
from app.audit.models import StudentAuditLog

__all__ = [
    "Base", "TimestampMixin",
    "User", "UserRole",
    "LectureGroup",
    "Group",
    "Lecture",
    "LectureImage",
    "Lab",
    "Submission", "SubmissionStatus",
    "LabSettings", "GradingScale",
    "AttestationSettings", "AttestationType",
    "Activity",
    "Attendance", "AttendanceStatus",
    "WorkType",
    "Work",
    "WorkSubmission",
    "ScheduleItem", "DayOfWeek", "LessonType", "WeekParity",
    "Lesson",
    "LessonGrade",
    "Subject",
    "TeacherSubjectAssignment",
    "ScheduleParserConfig",
    "ScheduleConflict",
    "ConflictType",
    "ParseHistory",
    "Note",
    "NoteEntityType",
    "NoteColor",
    "GroupReport",
    "ReportType",
    "ReportView",
    "StudentTransfer",
    "SettingsAuditLog",
    "StudentAuditLog",
]
