from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class GradingScale(str, Enum):
    FIVE = "5"
    TEN = "10"
    HUNDRED = "100"


class LabSettingsResponse(BaseModel):
    labs_count: int
    grading_scale: GradingScale
    default_max_grade: int
    is_configured: bool = True

    model_config = ConfigDict(from_attributes=True)


class LabSettingsUpdate(BaseModel):
    labs_count: int | None = Field(default=None, ge=1, le=50)
    grading_scale: GradingScale | None = None
    default_max_grade: int | None = None
