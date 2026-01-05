from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models.attestation_settings import AttestationType

# Base Schema
class ActivityBase(BaseModel):
    points: float = Field(..., description="Количество баллов (положительное - бонус, отрицательное - штраф)")
    description: str = Field(..., max_length=500, description="Описание активности/причины")
    attestation_type: AttestationType = Field(..., description="Тип аттестации")
    is_active: bool = Field(True, description="Активна ли запись")

# Create Schema
class ActivityCreate(ActivityBase):
    student_id: Optional[UUID] = Field(None, description="ID студента (если для одного)")
    group_id: Optional[UUID] = Field(None, description="ID группы (если для всей группы)")
    
    # Validation: either student_id or group_id must be provided
    # This logic will be handled in the endpoint or validator

# Update Schema
class ActivityUpdate(BaseModel):
    points: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

# Response Schema
class ActivityResponse(ActivityBase):
    id: UUID
    student_id: UUID
    batch_id: Optional[UUID]
    created_by_id: Optional[UUID]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

# Response with student info
class ActivityWithStudentResponse(ActivityResponse):
    student_name: Optional[str] = None
    group_name: Optional[str] = None

