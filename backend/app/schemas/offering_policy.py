"""API schemas for offering-scoped policy configuration."""

from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class OfferingPolicyPayload(BaseModel):
    total_labs: int = Field(ge=0)
    labs_required_first: int = Field(ge=0)
    labs_required_second_total: int = Field(ge=0)
    exam_admission_required_labs: int = Field(ge=0)
    automatic_enabled: bool = True
    automatic_places: int | None = Field(default=None, ge=0)
    automatic_required_labs_total: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_thresholds(self) -> "OfferingPolicyPayload":
        if self.labs_required_first > self.labs_required_second_total:
            raise ValueError("labs_required_first must be <= labs_required_second_total")
        if self.labs_required_second_total > self.total_labs:
            raise ValueError("labs_required_second_total must be <= total_labs")
        if self.exam_admission_required_labs > self.total_labs:
            raise ValueError("exam_admission_required_labs must be <= total_labs")
        if self.automatic_required_labs_total > self.total_labs:
            raise ValueError("automatic_required_labs_total must be <= total_labs")
        if self.automatic_enabled and self.automatic_required_labs_total < self.exam_admission_required_labs:
            raise ValueError("automatic_required_labs_total must be >= exam_admission_required_labs")
        return self


class OfferingPolicyResponse(OfferingPolicyPayload):
    offering_id: UUID
    source: str
    second_extra_required: int
    automatic_extra_required: int
