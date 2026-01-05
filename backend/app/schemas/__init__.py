from pydantic import BaseModel, Field
from .user import UserCreate, UserResponse, StudentInGroup, UserUpdate
from .group import GroupCreate, GroupResponse, StudentImport, GroupDetailResponse, StudentInGroupResponse
from .lab_settings import LabSettingsResponse, LabSettingsUpdate, GradingScale
from .attestation import (
    AttestationType,
    AttestationSettingsBase,
    AttestationSettingsCreate,
    AttestationSettingsUpdate,
    AttestationSettingsResponse,
    ComponentBreakdown,
    AttestationResult,
    AttestationResultResponse,
    GroupAttestationResponse,
    HyperionStudentRecord,
    HyperionExport,
    HyperionExportResponse,
)
from .attendance import (
    AttendanceStatusSchema,
    AttendanceCreate,
    AttendanceUpdate,
    AttendanceResponse,
    BulkAttendanceItem,
    BulkAttendanceCreate,
    BulkAttendanceResponse,
    AttendanceStatsResponse,
)
from .student import StudentLabSubmission, StudentStats, StudentProfileOut
from .admin import StatsResponse, DeleteResponse
from .activity import ActivityCreate, ActivityUpdate, ActivityResponse
from .schedule import (
    ScheduleItemCreate, ScheduleItemUpdate, ScheduleItemResponse,
    LessonCreate, LessonUpdate, LessonResponse,
    GenerateLessonsRequest, GenerateLessonsResponse,
)
from .lecture import (
    LectureCreate, LectureUpdate, LectureResponse,
    LectureListResponse, LectureImageResponse, PublicLinkResponse,
)
from .report import (
    ReportType,
    ReportCreate, ReportUpdate, ReportResponse, ReportListResponse,
    PublicReportData, PublicStudentData, StudentDetailData,
    AttendanceDistribution, LabProgress,
    AttendanceRecord, LabSubmission, ActivityRecord,
    PinVerifyRequest, PinVerifyResponse,
    ExportResponse, ReportViewStats, ReportViewRecord, ReportViewsResponse,
)

# Схема для обновления студента (Secure PATCH)
class StudentUpdate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)

__all__ = [
    "UserCreate", "UserResponse", "StudentInGroup", "UserUpdate",
    "GroupCreate", "GroupResponse", "StudentImport", "GroupDetailResponse", "StudentInGroupResponse",
    "StudentUpdate", "LabSettingsResponse", "LabSettingsUpdate", "GradingScale",
    # Attestation schemas
    "AttestationType",
    "AttestationSettingsBase",
    "AttestationSettingsCreate",
    "AttestationSettingsUpdate",
    "AttestationSettingsResponse",
    "ComponentBreakdown",
    "AttestationResult",
    "AttestationResultResponse",
    "GroupAttestationResponse",
    "HyperionStudentRecord",
    "HyperionExport",
    "HyperionExportResponse",
    # Attendance schemas
    "AttendanceStatusSchema",
    "AttendanceCreate",
    "AttendanceUpdate",
    "AttendanceResponse",
    "BulkAttendanceItem",
    "BulkAttendanceCreate",
    "BulkAttendanceResponse",
    "AttendanceStatsResponse",
    # Student schemas
    "StudentLabSubmission",
    "StudentStats",
    "StudentProfileOut",
    "StatsResponse",
    "DeleteResponse",
    # Activity schemas
    "ActivityCreate", "ActivityUpdate", "ActivityResponse",
    # Schedule schemas
    "ScheduleItemCreate", "ScheduleItemUpdate", "ScheduleItemResponse",
    "LessonCreate", "LessonUpdate", "LessonResponse",
    "GenerateLessonsRequest", "GenerateLessonsResponse",
    # Lecture schemas
    "LectureCreate", "LectureUpdate", "LectureResponse",
    "LectureListResponse", "LectureImageResponse", "PublicLinkResponse",
    # Report schemas
    "ReportType",
    "ReportCreate", "ReportUpdate", "ReportResponse", "ReportListResponse",
    "PublicReportData", "PublicStudentData", "StudentDetailData",
    "AttendanceDistribution", "LabProgress",
    "AttendanceRecord", "LabSubmission", "ActivityRecord",
    "PinVerifyRequest", "PinVerifyResponse",
    "ExportResponse", "ReportViewStats", "ReportViewRecord", "ReportViewsResponse",
]
