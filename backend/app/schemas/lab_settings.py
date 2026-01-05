from pydantic import BaseModel
from typing import Optional
from enum import Enum


class GradingScale(str, Enum):
    FIVE = "5"
    TEN = "10"
    HUNDRED = "100"


class LabSettingsResponse(BaseModel):
    labs_count: int
    grading_scale: GradingScale
    default_max_grade: int

    class Config:
        from_attributes = True


class LabSettingsUpdate(BaseModel):
    labs_count: Optional[int] = None
    grading_scale: Optional[GradingScale] = None
    default_max_grade: Optional[int] = None
