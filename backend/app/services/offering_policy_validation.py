"""Validation and normalization for offering-scoped academic policies."""

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from app.models.attestation_settings import AttestationType

OfferingPolicySource = Literal["explicit", "legacy"]


@dataclass(frozen=True)
class EffectiveOfferingPolicy:
    offering_id: UUID | None
    source: OfferingPolicySource
    total_labs: int
    labs_required_first: int
    labs_required_second_total: int
    exam_admission_required_labs: int
    automatic_enabled: bool
    automatic_places: int | None
    automatic_required_labs_total: int

    @property
    def labs_required_second_extra(self) -> int:
        return self.labs_required_second_total - self.labs_required_first

    @property
    def automatic_extra_required(self) -> int:
        return max(self.automatic_required_labs_total - self.exam_admission_required_labs, 0)

    def labs_required_for(self, attestation_type: AttestationType) -> int:
        if attestation_type == AttestationType.FIRST:
            return self.labs_required_first
        return self.labs_required_second_total


def validate_offering_policy(policy: EffectiveOfferingPolicy) -> EffectiveOfferingPolicy:
    """Validate cumulative lab thresholds before they enter read models."""
    if policy.total_labs < 0:
        raise ValueError("total_labs не может быть отрицательным")
    if not 0 <= policy.labs_required_first <= policy.labs_required_second_total <= policy.total_labs:
        raise ValueError("Пороги лабораторных должны быть: first <= second_total <= total_labs")
    if not 0 <= policy.exam_admission_required_labs <= policy.total_labs:
        raise ValueError("Порог допуска к экзамену должен быть в пределах общего числа лабораторных")
    if policy.automatic_places is not None and policy.automatic_places < 0:
        raise ValueError("Количество мест на автомат не может быть отрицательным")
    if not 0 <= policy.automatic_required_labs_total <= policy.total_labs:
        raise ValueError("Порог автомата должен быть в пределах общего числа лабораторных")
    if policy.automatic_enabled and policy.automatic_required_labs_total < policy.exam_admission_required_labs:
        raise ValueError("Порог автомата не может быть меньше порога допуска к экзамену")
    return policy
