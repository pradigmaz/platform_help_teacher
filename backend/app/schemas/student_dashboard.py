"""Schemas for student dashboard bootstrap payload."""

from pydantic import BaseModel

from app.schemas.announcement import AnnouncementListResponse


class StudentDashboardGroupInfo(BaseModel):
    id: str
    name: str
    code: str


class StudentDashboardProfile(BaseModel):
    id: str
    full_name: str
    username: str | None = None
    has_telegram: bool
    has_vk: bool
    role: str
    group: StudentDashboardGroupInfo | None = None


class StudentDashboardSemester(BaseModel):
    semester_start_date: str | None = None
    academic_year: int
    semester: int


class StudentDashboardAttendanceStats(BaseModel):
    total_classes: int
    present: int
    late: int
    excused: int
    absent: int
    attendance_rate: float


class StudentDashboardAttestationBreakdownComponent(BaseModel):
    score: float
    max: float


class StudentDashboardLabsBreakdown(StudentDashboardAttestationBreakdownComponent):
    count: int
    required: int


class StudentDashboardAttendanceBreakdown(StudentDashboardAttestationBreakdownComponent):
    ratio: float
    total_classes: int
    present: int
    late: int


class StudentDashboardActivityBreakdown(StudentDashboardAttestationBreakdownComponent):
    bonus_blocked: bool | None = None


class StudentDashboardAttestationBreakdown(BaseModel):
    labs: StudentDashboardLabsBreakdown
    attendance: StudentDashboardAttendanceBreakdown
    activity: StudentDashboardActivityBreakdown


class StudentDashboardAttestation(BaseModel):
    attestation_type: str
    subject_id: str | None = None
    total_score: float
    grade: str
    is_passing: bool
    max_points: int | None = None
    min_passing_points: int | None = None
    error: str | None = None
    calculation_status: str | None = None
    breakdown: StudentDashboardAttestationBreakdown | None = None


class StudentDashboardOverview(BaseModel):
    attendance_stats: StudentDashboardAttendanceStats
    labs: list[dict]
    attestation_type: str
    current_attestation: StudentDashboardAttestation | None = None


class StudentDashboardBootstrapResponse(BaseModel):
    profile: StudentDashboardProfile
    semester: StudentDashboardSemester
    announcements: list[AnnouncementListResponse]
    overview: StudentDashboardOverview
