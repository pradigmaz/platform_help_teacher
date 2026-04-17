from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.group_report import ReportType
from app.services.reports.group_report_collector import collect_group_report_data
from app.services.reports.student_detail_collector import collect_student_report_data


def _make_settings(attestation_type: AttestationType) -> AttestationSettings:
    return AttestationSettings(
        attestation_type=attestation_type,
        labs_weight=70.0,
        attendance_weight=20.0,
        activity_reserve=10.0,
        labs_count_first=4,
        labs_count_second=6,
        period_start_date=date(2025, 9, 1),
        period_end_date=date(2025, 12, 1),
    )


def _make_report(*, group_id, created_by, show_grades=True, show_attendance=True):
    return SimpleNamespace(
        group_id=group_id,
        created_by=created_by,
        report_type=ReportType.FULL.value,
        show_names=True,
        show_grades=show_grades,
        show_attendance=show_attendance,
        show_notes=False,
        show_rating=False,
    )


def _make_student(group_id):
    student = MagicMock()
    student.id = uuid4()
    student.group_id = group_id
    student.full_name = "Висягина Мирра Андреевна"
    student.subgroup = 1
    return student


@pytest.mark.asyncio
async def test_group_report_requires_subject_selection_when_period_has_multiple_subjects(mock_db):
    group_id = uuid4()
    report = _make_report(group_id=group_id, created_by=uuid4())
    student = _make_student(group_id)
    settings = _make_settings(AttestationType.SECOND)
    subjects = [
        SimpleNamespace(id=uuid4(), name="Матан", code="MAT"),
        SimpleNamespace(id=uuid4(), name="Физика", code="PHYS"),
    ]

    with (
        patch(
            "app.services.reports.group_report_collector.get_group",
            new=AsyncMock(return_value=SimpleNamespace(code="IT-11", name="ИТ-11", has_subgroups=True)),
        ),
        patch("app.services.reports.group_report_collector.get_user", new=AsyncMock(return_value=None)),
        patch("app.services.reports.group_report_collector.get_group_students", new=AsyncMock(return_value=[student])),
        patch(
            "app.services.reports.group_report_collector.get_semester_info",
            new=AsyncMock(return_value=(False, 70, 40, True)),
        ),
        patch(
            "app.services.reports.group_report_collector.get_semester_start_date",
            new=AsyncMock(return_value=date(2025, 9, 1)),
        ),
        patch(
            "app.services.reports.report_subject_helpers.list_group_subject_options_in_period",
            new=AsyncMock(return_value=subjects),
        ),
        patch(
            "app.services.attestation.service.AttestationService.get_or_create_settings",
            new=AsyncMock(return_value=settings),
        ),
    ):
        result = await collect_group_report_data(
            db=mock_db,
            report=report,
            attestation_type="second",
        )

    assert result.requires_subject is True
    assert result.selected_subject_id is None
    assert [subject.name for subject in result.available_subjects] == ["Матан", "Физика"]
    assert result.students == []
    assert result.subject_name is None


@pytest.mark.asyncio
async def test_student_report_uses_explicit_subject_for_second_attestation(mock_db):
    group_id = uuid4()
    report = _make_report(group_id=group_id, created_by=uuid4(), show_grades=False, show_attendance=False)
    student = _make_student(group_id)
    settings = _make_settings(AttestationType.SECOND)
    selected_subject = SimpleNamespace(id=uuid4(), name="Матан", code="MAT")
    other_subject = SimpleNamespace(id=uuid4(), name="Физика", code="PHYS")
    score_mock = AsyncMock(
        return_value=SimpleNamespace(
            total_score=52.0,
            grade="хор",
            is_passing=True,
            max_points=70,
            min_passing_points=40,
            breakdown=SimpleNamespace(
                labs_score=0.0,
                attendance_score=0.0,
                activity_score=0.0,
                labs_count=0,
                labs_required=0,
            ),
        )
    )

    with (
        patch("app.services.reports.student_detail_collector.get_user", new=AsyncMock(return_value=student)),
        patch(
            "app.services.reports.student_detail_collector.get_group",
            new=AsyncMock(return_value=SimpleNamespace(code="IT-11")),
        ),
        patch(
            "app.services.reports.student_detail_collector.get_semester_info",
            new=AsyncMock(return_value=(False, 70, 40, True)),
        ),
        patch(
            "app.services.reports.report_subject_helpers.list_group_subject_options_in_period",
            new=AsyncMock(return_value=[selected_subject, other_subject]),
        ),
        patch(
            "app.services.attestation.service.AttestationService.get_or_create_settings",
            new=AsyncMock(return_value=settings),
        ),
        patch("app.services.attestation.service.AttestationService.calculate_student_score", score_mock),
    ):
        result = await collect_student_report_data(
            db=mock_db,
            report=report,
            student_id=student.id,
            attestation_type="second",
            subject_id=selected_subject.id,
        )

    assert result is not None
    assert result.requires_subject is True
    assert result.selected_subject_id == selected_subject.id
    assert result.subject_name == "Матан"
    score_mock.assert_awaited_once_with(
        student_id=student.id,
        group_id=group_id,
        attestation_type=AttestationType.SECOND,
        subject_id=selected_subject.id,
    )
