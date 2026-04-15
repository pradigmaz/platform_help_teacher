from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.lab import Lab
from app.models.lesson_grade import LessonGrade
from app.models.submission import Submission, SubmissionStatus
from app.services.reports.report_lab_detail_service import get_student_lab_submissions
from app.services.reports.report_lab_service import ReportLabState, get_group_labs_stats, get_lab_progress


def _make_settings(*, total_labs: int = 4) -> AttestationSettings:
    return AttestationSettings(
        attestation_type=AttestationType.FIRST,
        labs_weight=70.0,
        attendance_weight=20.0,
        activity_reserve=10.0,
        labs_count_first=total_labs,
    )


def _make_student(*, subgroup: int | None = None):
    student = MagicMock()
    student.id = uuid4()
    student.subgroup = subgroup
    return student


def _make_lab(work_number: int, *, title: str, subject_id):
    lab = Lab(
        id=uuid4(),
        number=work_number,
        title=title,
        subject_id=subject_id,
        max_grade=5,
        is_published=True,
    )
    lab.created_at = datetime.now(UTC)
    return lab


def _make_grade(work_number: int, grade: int) -> LessonGrade:
    lesson_grade = LessonGrade(
        id=uuid4(),
        lesson_id=uuid4(),
        student_id=uuid4(),
        work_number=work_number,
        grade=grade,
    )
    lesson_grade.created_at = datetime.now(UTC)
    lesson_grade.lab_subject_id = uuid4()
    return lesson_grade


@pytest.mark.asyncio
async def test_group_labs_stats_use_attestation_result_and_normalized_fallback(mock_db):
    settings = _make_settings(total_labs=4)
    group_id = uuid4()
    subject_id = uuid4()
    first_student = _make_student(subgroup=1)
    second_student = _make_student(subgroup=2)
    results_map = {
        first_student.id: SimpleNamespace(
            breakdown=SimpleNamespace(
                labs_count=3,
                labs_required=4,
            )
        )
    }

    with (
        patch(
            "app.services.reports.report_lab_service._resolve_subject_id",
            new=AsyncMock(return_value=(True, subject_id)),
        ),
        patch(
            "app.services.reports.report_lab_service._load_completed_states_by_student",
            new=AsyncMock(
                return_value={
                    first_student.id: {1: ReportLabState(grade=5, is_completed=True)},
                    second_student.id: {1: ReportLabState(grade=5, is_completed=True)},
                }
            ),
        ),
    ):
        stats = await get_group_labs_stats(
            mock_db,
            group_id,
            [first_student, second_student],
            settings,
            results_map,
        )

    assert stats[first_student.id] == {"completed": 3, "total": 4}
    assert stats[second_student.id] == {"completed": 1, "total": 4}


@pytest.mark.asyncio
async def test_group_lab_progress_counts_journal_only_completion(mock_db):
    settings = _make_settings(total_labs=3)
    group_id = uuid4()
    subject_id = uuid4()
    students = [_make_student(subgroup=1), _make_student(subgroup=1), _make_student(subgroup=2)]
    catalog = {
        1: _make_lab(1, title="Лаба 1", subject_id=subject_id),
        2: _make_lab(2, title="Лаба 2", subject_id=subject_id),
        3: _make_lab(3, title="Лаба 3", subject_id=subject_id),
    }
    states = {
        students[0].id: {1: ReportLabState(grade=5, is_completed=True)},
        students[1].id: {
            1: ReportLabState(grade=4, is_completed=True),
            2: ReportLabState(grade=5, is_completed=True),
        },
        students[2].id: {},
    }

    with (
        patch(
            "app.services.reports.report_lab_service._resolve_subject_id",
            new=AsyncMock(return_value=(True, subject_id)),
        ),
        patch(
            "app.services.reports.report_lab_service._load_completed_states_by_student",
            new=AsyncMock(return_value=states),
        ),
        patch(
            "app.services.reports.report_lab_service._load_lab_catalog_by_number",
            new=AsyncMock(return_value=catalog),
        ),
    ):
        progress_all, by_subgroup = await get_lab_progress(
            mock_db,
            group_id,
            students,
            settings,
            has_subgroups=True,
        )

    assert [item.completed_count for item in progress_all] == [2, 1, 0]
    assert [item.lab_name for item in progress_all] == ["Лаба 1", "Лаба 2", "Лаба 3"]
    assert by_subgroup is not None
    assert [item.completed_count for item in by_subgroup["1"]] == [2, 1, 0]
    assert [item.completed_count for item in by_subgroup["2"]] == [0, 0, 0]


@pytest.mark.asyncio
async def test_student_lab_submissions_include_journal_only_grade(mock_db):
    settings = _make_settings(total_labs=2)
    group_id = uuid4()
    subject_id = uuid4()
    student_id = uuid4()
    journal_grade = _make_grade(2, 5)
    rejected_submission = Submission(
        id=uuid4(),
        user_id=student_id,
        lab_id=uuid4(),
        status=SubmissionStatus.REQ_CHANGES,
        is_manual=True,
        grade=2,
    )
    rejected_submission.created_at = datetime.now(UTC)

    with (
        patch(
            "app.services.reports.report_lab_detail_service._resolve_subject_id",
            new=AsyncMock(return_value=(True, subject_id)),
        ),
        patch(
            "app.services.reports.report_lab_detail_service._load_lab_catalog_by_number",
            new=AsyncMock(
                return_value={
                    1: _make_lab(1, title="Лаба 1", subject_id=subject_id),
                    2: _make_lab(2, title="Лаба 2", subject_id=subject_id),
                }
            ),
        ),
        patch(
            "app.services.reports.report_lab_detail_service._load_student_journal_grades",
            new=AsyncMock(return_value={2: journal_grade}),
        ),
        patch(
            "app.services.reports.report_lab_detail_service._load_student_submissions_by_work",
            new=AsyncMock(return_value={1: rejected_submission}),
        ),
    ):
        slots = await get_student_lab_submissions(mock_db, group_id, student_id, settings)

    assert len(slots) == 2
    assert slots[0].lab_number == 1
    assert slots[0].is_submitted is False
    assert slots[0].grade == 2
    assert slots[1].lab_number == 2
    assert slots[1].is_submitted is True
    assert slots[1].grade == 5
