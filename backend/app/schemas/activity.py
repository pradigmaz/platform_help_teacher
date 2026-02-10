from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.attestation_settings import AttestationType


# Base Schema
class ActivityBase(BaseModel):
    points: float = Field(..., description="Количество баллов (положительное - бонус, отрицательное - штраф)")
    description: str = Field(..., max_length=500, description="Описание активности/причины")
    attestation_type: AttestationType = Field(..., description="Тип аттестации")
    is_active: bool = Field(True, description="Активна ли запись")

# Create Schema
class ActivityCreate(ActivityBase):
    student_id: UUID | None = Field(None, description="ID студента (если для одного)")
    group_id: UUID | None = Field(None, description="ID группы (если для всей группы)")

    # Validation: either student_id or group_id must be provided
    # This logic will be handled in the endpoint or validator

# Update Schema
class ActivityUpdate(BaseModel):
    points: float | None = None
    description: str | None = None
    is_active: bool | None = None

# Response Schema
class ActivityResponse(ActivityBase):
    id: UUID
    student_id: UUID
    batch_id: UUID | None
    created_by_id: UUID | None
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

# Response with student info
class ActivityWithStudentResponse(ActivityResponse):
    student_name: str | None = None
    group_name: str | None = None

