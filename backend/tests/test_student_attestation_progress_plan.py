from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.api.v1.endpoints.student.attestation import resolve_student_lab_progress_plan
from app.models.attestation_settings import AttestationSettings, AttestationType
from app.services.attestation.student_automatic_progress import StudentAutomaticProgress
from app.services.attestation.student_lab_progress_plan import build_student_lab_progress_plan


def test_build_student_lab_progress_plan_returns_manual_thresholds_and_derived_automatic_gap():
    plan = build_student_lab_progress_plan(
        total_labs=10,
        first_required=4,
        second_required=4,
        automatic_enabled=True,
        automatic_places=3,
        completed_count=7,
        automatic_remaining=3,
        automatic_queue_position=2,
        automatic_is_winner=True,
    )

    assert plan == {
        "total_required": 10,
        "first_required": 4,
        "second_extra_required": 4,
        "second_total_required": 8,
        "automatic_extra_required": 2,
        "automatic_enabled": True,
        "automatic_places": 3,
        "completed_count": 7,
        "automatic_remaining": 3,
        "automatic_queue_position": 2,
        "automatic_is_winner": True,
        "automatic_completion_at": None,
        "automatic_reason": None,
        "automatic_declined": False,
    }


def test_build_student_lab_progress_plan_clamps_negative_automatic_gap_to_zero():
    plan = build_student_lab_progress_plan(
        total_labs=8,
        first_required=5,
        second_required=4,
        automatic_enabled=False,
        automatic_places=None,
        completed_count=9,
        automatic_reason="disabled",
    )

    assert plan["second_total_required"] == 9
    assert plan["automatic_extra_required"] == 0
    assert plan["automatic_enabled"] is False
    assert plan["automatic_places"] is None
    assert plan["completed_count"] == 9
    assert plan["automatic_remaining"] == 0
    assert plan["automatic_reason"] == "disabled"
    assert plan["automatic_declined"] is False


@pytest.mark.asyncio
async def test_resolve_student_lab_progress_plan_disables_automatic_when_offering_is_not_exam():
    db = AsyncMock()
    current_user = SimpleNamespace(id=uuid4(), group_id=uuid4())
    settings = AttestationSettings(
        attestation_type=AttestationType.FIRST,
        labs_count_first=4,
        labs_count_second=4,
    )
    lab_settings = SimpleNamespace(labs_count=10, automatic_enabled=True, automatic_places=2)
    automatic_progress = StudentAutomaticProgress(
        completed_count=6,
        automatic_remaining=4,
        queue_position=None,
        is_winner=None,
        completion_at=None,
        automatic_reason="not_exam",
        automatic_declined=False,
    )

    from app.services.offering_policy_validation import EffectiveOfferingPolicy
    policy = EffectiveOfferingPolicy(
        offering_id=uuid4(),
        source="legacy",
        total_labs=10,
        labs_required_first=4,
        labs_required_second_total=8,
        exam_admission_required_labs=8,
        automatic_enabled=True,
        automatic_places=2,
        automatic_required_labs_total=10,
    )

    with (
        patch(
            "app.api.v1.endpoints.student.attestation.resolve_student_automatic_offering",
            new=AsyncMock(return_value=SimpleNamespace(offering=SimpleNamespace(), reason=None)),
        ),
        patch(
            "app.api.v1.endpoints.student.attestation.resolve_offering_policy",
            new=AsyncMock(return_value=policy),
        ),
        patch(
            "app.api.v1.endpoints.student.attestation.resolve_student_automatic_progress",
            new=AsyncMock(return_value=automatic_progress),
        ),
    ):
        plan = await resolve_student_lab_progress_plan(db, current_user)

    assert plan["automatic_enabled"] is False
    assert plan["automatic_reason"] == "not_exam"
    assert plan["completed_count"] == 6
    assert plan["automatic_remaining"] == 4


@pytest.mark.asyncio
async def test_resolve_student_lab_progress_plan_keeps_automatic_visible_for_declined_student():
    db = AsyncMock()
    current_user = SimpleNamespace(id=uuid4(), group_id=uuid4())
    settings = AttestationSettings(
        attestation_type=AttestationType.FIRST,
        labs_count_first=4,
        labs_count_second=4,
    )
    lab_settings = SimpleNamespace(labs_count=10, automatic_enabled=True, automatic_places=2)
    automatic_progress = StudentAutomaticProgress(
        completed_count=10,
        automatic_remaining=0,
        queue_position=None,
        is_winner=False,
        completion_at=None,
        automatic_reason="refused",
        automatic_declined=True,
    )

    from app.services.offering_policy_validation import EffectiveOfferingPolicy
    policy = EffectiveOfferingPolicy(
        offering_id=uuid4(),
        source="legacy",
        total_labs=10,
        labs_required_first=4,
        labs_required_second_total=8,
        exam_admission_required_labs=8,
        automatic_enabled=True,
        automatic_places=2,
        automatic_required_labs_total=10,
    )

    with (
        patch(
            "app.api.v1.endpoints.student.attestation.resolve_student_automatic_offering",
            new=AsyncMock(return_value=SimpleNamespace(offering=SimpleNamespace(), reason=None)),
        ),
        patch(
            "app.api.v1.endpoints.student.attestation.resolve_offering_policy",
            new=AsyncMock(return_value=policy),
        ),
        patch(
            "app.api.v1.endpoints.student.attestation.resolve_student_automatic_progress",
            new=AsyncMock(return_value=automatic_progress),
        ),
    ):
        plan = await resolve_student_lab_progress_plan(db, current_user)

    assert plan["automatic_enabled"] is True
    assert plan["automatic_reason"] == "refused"
    assert plan["automatic_declined"] is True
