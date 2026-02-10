from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class StudentLabSubmission(BaseModel):
    lab_id: UUID
    lab_title: str
    status: str | None = None
    grade: int | None = None
    max_grade: int
    deadline_5_lessons: int | None = None
    deadline_4_lessons: int | None = None
    submitted_at: datetime | None = None
    feedback: str | None = None
    is_overdue: bool = False  # Просрочено


class StudentStats(BaseModel):
    labs_total: int = 0
    labs_submitted: int = 0
    labs_accepted: int = 0
    labs_rejected: int = 0
    labs_pending: int = 0
    labs_overdue: int = 0

    points_earned: int = 0
    points_max: int = 0
    points_percent: float = 0.0

    # Рейтинг в группе
    group_rank: int | None = None
    group_total: int = 0  # Всего студентов в группе
    group_percentile: float | None = None  # Процентиль в группе


class StudentProfileOut(BaseModel):
    id: UUID
    full_name: str
    username: str | None = None
    telegram_id: int | None = None
    vk_id: int | None = None
    group_name: str | None = None
    group_id: UUID | None = None
    is_active: bool
    created_at: datetime
    labs: list[StudentLabSubmission] = []
    stats: StudentStats = StudentStats()

    class Config:
        from_attributes = True
