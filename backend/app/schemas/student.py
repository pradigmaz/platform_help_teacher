from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

class StudentLabSubmission(BaseModel):
    lab_id: UUID
    lab_title: str
    status: Optional[str] = None
    grade: Optional[int] = None
    max_grade: int
    deadline: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    feedback: Optional[str] = None
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
    group_rank: Optional[int] = None
    group_total: int = 0  # Всего студентов в группе
    group_percentile: Optional[float] = None  # Процентиль в группе

class StudentProfileOut(BaseModel):
    id: UUID
    full_name: str
    username: Optional[str] = None
    telegram_id: Optional[int] = None
    vk_id: Optional[int] = None
    group_name: Optional[str] = None
    group_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime
    labs: List[StudentLabSubmission] = []
    stats: StudentStats = StudentStats()

    class Config:
        from_attributes = True

