from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.api.v1.endpoints.student.attestation import resolve_student_lab_progress_plan
from app.api.v1.endpoints.student.bootstrap import resolve_current_attestation


@pytest.mark.asyncio
async def test_bootstrap_multi_subject_attestation_does_not_return_unscoped_lab_plan():
    user = SimpleNamespace(group_id=uuid4())
    subjects = [
        SimpleNamespace(id=uuid4(), name="КС", code=None),
        SimpleNamespace(id=uuid4(), name="Внедрение ИС", code=None),
    ]

    with (
        patch(
            "app.api.v1.endpoints.student.bootstrap.list_student_attestation_subjects",
            new=AsyncMock(return_value=subjects),
        ),
        patch(
            "app.api.v1.endpoints.student.bootstrap.resolve_student_lab_progress_plan",
            new=AsyncMock(side_effect=AssertionError("unscoped plan must not be built")),
        ),
    ):
        payload = await resolve_current_attestation(AsyncMock(), user, "first", [])

    assert payload is not None
    assert payload["subject_id"] is None
    assert payload["lab_progress_plan"] is None


@pytest.mark.asyncio
async def test_student_lab_progress_plan_does_not_fallback_when_offering_is_missing():
    user = SimpleNamespace(group_id=uuid4())
    resolve_policy = AsyncMock()

    with (
        patch(
            "app.api.v1.endpoints.student.attestation.resolve_student_automatic_offering",
            new=AsyncMock(return_value=SimpleNamespace(offering=None, reason="offering_missing")),
        ),
        patch("app.api.v1.endpoints.student.attestation.resolve_offering_policy", new=resolve_policy),
    ):
        payload = await resolve_student_lab_progress_plan(AsyncMock(), user, subject_id=uuid4())

    assert payload is None
    resolve_policy.assert_not_awaited()
