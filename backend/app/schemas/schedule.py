"""
Схемы для расписания и занятий.
"""

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.schedule import DayOfWeek, LessonType, WeekParity
from app.schemas.schedule_parser import ScheduleConflictResponse

AttendanceSummaryState = Literal["hidden", "not_applicable", "unmarked", "partial", "complete"]

# === ScheduleItem ===


class ScheduleItemBase(BaseModel):
    day_of_week: DayOfWeek
    lesson_number: int = Field(ge=1, le=8)
    lesson_type: LessonType
    subject: str | None = None
    subject_id: UUID | None = None
    offering_id: UUID | None = None
    room: str | None = None
    teacher_id: UUID | None = None
    start_date: date
    end_date: date | None = None
    week_parity: WeekParity | None = None
    subgroup: int | None = Field(None, ge=1, le=2)


class ScheduleItemCreate(ScheduleItemBase):
    group_id: UUID


class ScheduleItemUpdate(BaseModel):
    day_of_week: DayOfWeek | None = None
    lesson_number: int | None = Field(None, ge=1, le=8)
    lesson_type: LessonType | None = None
    subject: str | None = None
    subject_id: UUID | None = None
    offering_id: UUID | None = None
    room: str | None = None
    teacher_id: UUID | None = None
    start_date: date | None = None
    end_date: date | None = None
    week_parity: WeekParity | None = None
    subgroup: int | None = Field(None, ge=1, le=2)
    is_active: bool | None = None


class ScheduleItemResponse(ScheduleItemBase):
    id: UUID
    group_id: UUID
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# === Lesson ===


class LessonBase(BaseModel):
    date: date
    lesson_number: int = Field(ge=1, le=8)
    lesson_type: LessonType
    subject_id: UUID | None = None
    offering_id: UUID | None = None
    topic: str | None = None
    room: str | None = None
    work_id: UUID | None = None
    subgroup: int | None = Field(None, ge=1, le=2)


class LessonCreate(LessonBase):
    group_id: UUID
    schedule_item_id: UUID | None = None


class LessonUpdate(BaseModel):
    subject_id: UUID | None = None
    offering_id: UUID | None = None
    topic: str | None = None
    work_id: UUID | None = None
    work_number: int | None = Field(None, ge=1, le=20, description="Номер лабы/практики")
    is_cancelled: bool | None = None
    cancellation_reason: str | None = None
    ended_early: bool | None = None


class LessonAttendanceSummaryResponse(BaseModel):
    state: AttendanceSummaryState
    marked_count: int = 0
    expected_count: int = 0
    is_past: bool


class LessonResponse(LessonBase):
    id: UUID
    group_id: UUID
    schedule_item_id: UUID | None
    is_cancelled: bool
    cancellation_reason: str | None
    work_number: int | None = None
    ended_early: bool = False
    subject_name: str | None = None
    group_name: str | None = None
    summary: LessonAttendanceSummaryResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class ScheduleAttendanceUpdate(BaseModel):
    student_id: UUID
    status: str | None = None


class ScheduleGradeUpdate(BaseModel):
    student_id: UUID
    grade: int | None = Field(None, ge=2, le=5)
    work_number: int | None = Field(None, ge=1, le=20, description="Номер сдаваемой работы")


class LessonSheetSaveRequest(BaseModel):
    topic: str | None = None
    lesson_work_number: int | None = Field(None, ge=1, le=20, description="Базовый номер работы пары")
    status: Literal["normal", "cancelled", "early"]
    attendance_updates: list[ScheduleAttendanceUpdate] = Field(default_factory=list)
    grade_updates: list[ScheduleGradeUpdate] = Field(default_factory=list)


class GroupedLectureSheetSaveItem(BaseModel):
    lesson_id: UUID
    attendance_updates: list[ScheduleAttendanceUpdate] = Field(default_factory=list)


class GroupedLectureSheetSaveRequest(BaseModel):
    status: Literal["normal", "cancelled", "early"]
    topic: str | None = None
    items: list[GroupedLectureSheetSaveItem] = Field(default_factory=list)


class LessonSheetAttendanceResponse(BaseModel):
    student_id: UUID
    status: str


class LessonSheetGradeResponse(BaseModel):
    student_id: UUID
    grade: int | None = None
    work_number: int | None = None
    has_conflict: bool = False
    conflict_count: int = 0
    grade_items: list[dict[str, int | None]] = Field(default_factory=list)


class LessonSheetSaveResponse(BaseModel):
    lesson: LessonResponse
    attendance: list[LessonSheetAttendanceResponse]
    grades: list[LessonSheetGradeResponse]


class GroupedLectureSheetItemResponse(BaseModel):
    lesson_id: UUID
    attendance: list[LessonSheetAttendanceResponse]


class GroupedLectureSheetSaveResponse(BaseModel):
    items: list[GroupedLectureSheetItemResponse]


class GroupedLectureGroupResponse(BaseModel):
    id: UUID
    name: str
    lesson_id: UUID


class GroupedLectureAttendanceSummaryResponse(BaseModel):
    state: AttendanceSummaryState
    marked_count: int = 0
    expected_count: int = 0
    is_past: bool


class GroupedLectureResponse(BaseModel):
    date: date
    lesson_number: int
    subject_id: UUID | None = None
    subject_name: str | None = None
    topic: str | None = None
    room: str | None = None
    is_cancelled: bool = False
    ended_early: bool = False
    groups: list[GroupedLectureGroupResponse]
    summary: GroupedLectureAttendanceSummaryResponse | None = None


class ScheduleParseStatusResponse(BaseModel):
    is_running: bool
    status: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    lessons_created: int | None = None
    lessons_updated: int | None = None
    lessons_skipped: int | None = None
    conflicts_created: int | None = None
    error_message: str | None = None
    last_run: str | None = None


class ScheduleViewResponse(BaseModel):
    """Aggregate payload for admin schedule page."""

    parse_status: ScheduleParseStatusResponse
    conflicts: list[ScheduleConflictResponse]
    lessons: list[LessonResponse]
    grouped_lectures: list[GroupedLectureResponse]
    last_updated: str


# === Bulk operations ===


class GenerateLessonsRequest(BaseModel):
    """Запрос на генерацию занятий из расписания"""

    group_id: UUID
    start_date: date
    end_date: date


class GenerateLessonsResponse(BaseModel):
    """Ответ на генерацию занятий"""

    created_count: int
    lessons: list[LessonResponse]


class ParseScheduleRequest(BaseModel):
    """Запрос на парсинг расписания"""

    teacher_name: str
    start_date: date
    end_date: date | None = None  # По умолчанию - сегодня


class ParseScheduleResponse(BaseModel):
    """Результат парсинга"""

    total_parsed: int
    groups_created: int
    lessons_created: int
    lessons_updated: int = 0
    lessons_skipped: int
    conflicts_created: int = 0
    subjects_created: int = 0
    assignments_created: int = 0
    groups: list[str]
    subjects: list[str] = []
    semester_end_detected: bool = False
    last_lesson_date: str | None = None
    empty_weeks_count: int = 0
