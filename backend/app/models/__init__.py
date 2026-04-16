# SQLAlchemy models
from app.audit.models import StudentAuditLog

from .activity import Activity
from .announcement import Announcement
from .automatic_pass_refusal import AutomaticPassRefusal
from .attendance import Attendance, AttendanceStatus
from .attestation_settings import AttestationSettings, AttestationType
from .backup_settings import BackupSettings
from .base import Base, TimestampMixin
from .device import Device
from .feedback import Feedback, FeedbackStatus, FeedbackType
from .feedback_attachment import FeedbackAttachment
from .group import Group
from .group_report import GroupReport, ReportType
from .group_subject_offering import FinalControlType, GroupSubjectOffering
from .lab import Lab
from .lab_deadline_extension import LabDeadlineExtension
from .lab_settings import GradingScale, LabSettings
from .lecture import Lecture
from .lecture_group import LectureGroup  # Must be before Group and Lecture
from .lecture_image import LectureImage
from .lesson import Lesson
from .lesson_grade import LessonGrade
from .note import EntityType as NoteEntityType
from .note import Note, NoteColor
from .notification_settings import NotificationSettings
from .parse_history import ParseHistory
from .report_view import ReportView
from .schedule import DayOfWeek, LessonType, ScheduleItem, WeekParity
from .schedule_conflict import ConflictType, ScheduleConflict
from .schedule_parser_config import ScheduleParserConfig
from .settings_audit import SettingsAuditLog
from .student_transfer import StudentTransfer
from .subject import Subject
from .submission import Submission, SubmissionStatus
from .teacher_subject import TeacherSubjectAssignment
from .user import User, UserRole
from .work import Work
from .work_submission import WorkSubmission
from .work_type import WorkType

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "UserRole",
    "Device",
    "LectureGroup",
    "Group",
    "Lecture",
    "LectureImage",
    "Lab",
    "LabDeadlineExtension",
    "Submission",
    "SubmissionStatus",
    "LabSettings",
    "GradingScale",
    "AttestationSettings",
    "AttestationType",
    "Activity",
    "Attendance",
    "AttendanceStatus",
    "WorkType",
    "Work",
    "WorkSubmission",
    "ScheduleItem",
    "DayOfWeek",
    "LessonType",
    "WeekParity",
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
    "BackupSettings",
    "Feedback",
    "FeedbackType",
    "FeedbackStatus",
    "FeedbackAttachment",
    "Announcement",
    "NotificationSettings",
    "StudentAuditLog",
    "GroupSubjectOffering",
    "FinalControlType",
    "AutomaticPassRefusal",
]
