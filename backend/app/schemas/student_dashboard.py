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


class StudentDashboardLabProgressPlan(BaseModel):
    total_required: int
    first_required: int
    second_extra_required: int
    second_total_required: int
    automatic_extra_required: int
    automatic_enabled: bool = True
    automatic_places: int | None = None
    completed_count: int = 0
    automatic_remaining: int = 0
    automatic_queue_position: int | None = None
    automatic_is_winner: bool | None = None
    automatic_completion_at: str | None = None
    automatic_reason: str | None = None
    automatic_declined: bool = False


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
    lab_progress_plan: StudentDashboardLabProgressPlan | None = None
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
