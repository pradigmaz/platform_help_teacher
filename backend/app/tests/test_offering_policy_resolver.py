from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.models.attestation_settings import AttestationType
from app.models.group_subject_offering import FinalControlType
from app.services.offering_policy_resolver import resolve_offering_policy
from app.services.offering_policy_validation import EffectiveOfferingPolicy, validate_offering_policy


class ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


@pytest.mark.asyncio
async def test_resolve_offering_policy_prefers_explicit_row():
    offering_id = uuid4()
    row = SimpleNamespace(
        offering_id=offering_id,
        total_labs=12,
        labs_required_first=4,
        labs_required_second_total=9,
        exam_admission_required_labs=9,
        automatic_enabled=True,
        automatic_places=2,
        automatic_required_labs_total=11,
    )
    db = SimpleNamespace(execute=AsyncMock(return_value=ScalarResult(row)))
    offering = SimpleNamespace(id=offering_id, final_control_type=FinalControlType.EXAM)

    policy = await resolve_offering_policy(db, offering)

    assert policy.source == "explicit"
    assert policy.total_labs == 12
    assert policy.labs_required_for(AttestationType.SECOND) == 9
    assert policy.automatic_extra_required == 2


@pytest.mark.asyncio
async def test_resolve_offering_policy_derives_legacy_fallback_when_row_missing():
    offering_id = uuid4()
    db = SimpleNamespace(
        execute=AsyncMock(
            side_effect=[
                ScalarResult(None),
                ScalarResult(SimpleNamespace(labs_count=15, automatic_enabled=True, automatic_places=3)),
                ScalarResult(SimpleNamespace(labs_count_first=5)),
                ScalarResult(SimpleNamespace(labs_count_second=7)),
            ]
        )
    )
    offering = SimpleNamespace(id=offering_id, final_control_type=FinalControlType.EXAM)

    policy = await resolve_offering_policy(db, offering)

    assert policy.source == "legacy"
    assert policy.total_labs == 15
    assert policy.labs_required_first == 5
    assert policy.labs_required_second_total == 12
    assert policy.exam_admission_required_labs == 12
    assert policy.automatic_required_labs_total == 15


def test_validate_offering_policy_rejects_invalid_thresholds():
    policy = EffectiveOfferingPolicy(
        offering_id=uuid4(),
        source="explicit",
        total_labs=8,
        labs_required_first=5,
        labs_required_second_total=4,
        exam_admission_required_labs=4,
        automatic_enabled=True,
        automatic_places=1,
        automatic_required_labs_total=8,
    )

    with pytest.raises(ValueError, match="first <= second_total"):
        validate_offering_policy(policy)
