from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.models.attestation_settings import AttestationType
from app.services.offering_policy_validation import EffectiveOfferingPolicy
from app.services.reports.report_lab_detail_service import _load_student_submissions_by_work
from app.services.reports.report_lab_service import _load_lab_catalog_by_number, get_lab_progress


@pytest.mark.asyncio
async def test_report_lab_progress_uses_offering_total_labs():
    group_id = uuid4()
    subject_id = uuid4()
    settings = SimpleNamespace(attestation_type=AttestationType.SECOND)
    policy = EffectiveOfferingPolicy(
        offering_id=uuid4(),
        source="explicit",
        total_labs=6,
        labs_required_first=2,
        labs_required_second_total=4,
        exam_admission_required_labs=4,
        automatic_enabled=True,
        automatic_places=1,
        automatic_required_labs_total=6,
    )

    with (
        patch(
            "app.services.reports.report_lab_service._resolve_subject_id",
            new=AsyncMock(return_value=(True, subject_id)),
        ),
        patch(
            "app.services.reports.report_lab_service.resolve_offering_policy_for_group_subject",
            new=AsyncMock(return_value=policy),
        ),
        patch(
            "app.services.reports.report_lab_service._load_completed_states_by_student", new=AsyncMock(return_value={})
        ),
        patch("app.services.reports.report_lab_service._load_lab_catalog_by_number", new=AsyncMock(return_value={})),
    ):
        progress, by_subgroup = await get_lab_progress(
            AsyncMock(),
            group_id,
            [],
            settings,
            has_subgroups=False,
            subject_id=subject_id,
        )

    assert by_subgroup is None
    assert [row.lab_name for row in progress] == [f"Лаб. {number}" for number in range(1, 7)]


class _EmptyScalars:
    def scalars(self):
        return self

    def all(self):
        return []


class _EmptyRows:
    def all(self):
        return []


@pytest.mark.asyncio
async def test_report_lab_catalog_filters_by_selected_subject():
    subject_id = uuid4()
    captured = {}

    async def execute(query):
        captured["query"] = query
        return _EmptyScalars()

    await _load_lab_catalog_by_number(SimpleNamespace(execute=execute), 6, subject_id)

    query_text = str(captured["query"])
    assert "labs.subject_id" in query_text


@pytest.mark.asyncio
async def test_report_lab_submissions_filter_by_selected_subject():
    subject_id = uuid4()
    captured = {}

    async def execute(query):
        captured["query"] = query
        return _EmptyRows()

    await _load_student_submissions_by_work(SimpleNamespace(execute=execute), uuid4(), 6, subject_id)

    query_text = str(captured["query"])
    assert "labs.subject_id" in query_text
