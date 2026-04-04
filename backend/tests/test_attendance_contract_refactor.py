"""Contract tests for the shared attendance refactor."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.attendance import Attendance, AttendanceStatus
from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.group_report import ReportType
from app.models.lesson import Lesson
from app.models.user import User
from app.schemas.report import AttendanceDistribution, AttendanceStats
from app.services.attendance_contract import (
    AttendanceCounts,
    StudentAttendanceSnapshot,
    build_student_attendance_snapshots,
)
from app.services.attestation.batch import BatchScoreCalculator
from app.services.attestation.student_score import StudentScoreCalculator
from app.services.export.attendance_helpers import collect_attendance_rows
from app.services.reports.data_collector import ReportDataCollector
from app.services.reports.student_detail_collector import collect_student_report_data


def _make_settings(*, start: date, end: date) -> AttestationSettings:
    return AttestationSettings(
        attestation_type=AttestationType.FIRST,
        labs_weight=70.0,
        attendance_weight=20.0,
        activity_reserve=10.0,
        late_coef=0.5,
        absent_coef=0.0,
        period_start_date=start,
        period_end_date=end,
        labs_count_first=1,
        expected_lessons_per_week=0,
    )


def _make_student(*, subgroup: int | None = None) -> MagicMock:
    student = MagicMock(spec=User)
    student.id = uuid4()
    student.full_name = "Иванов Иван Иванович"
    student.subgroup = subgroup
    student.group_id = uuid4()
    return student


def _make_lesson(*, lesson_date: date, lesson_number: int, subgroup: int | None = None) -> MagicMock:
    lesson = MagicMock(spec=Lesson)
    lesson.id = uuid4()
    lesson.date = lesson_date
    lesson.lesson_number = lesson_number
    lesson.subgroup = subgroup
    lesson.topic = f"Lesson {lesson_number}"
    lesson.lesson_type = SimpleNamespace(value="lecture")
    return lesson


def _make_attendance(*, student_id, lesson, status: AttendanceStatus) -> MagicMock:
    record = MagicMock(spec=Attendance)
    record.student_id = student_id
    record.lesson_id = lesson.id
    record.date = lesson.date
    record.lesson_number = lesson.lesson_number
    record.status = status
    return record


def _make_report(*, group_id, created_by, show_grades: bool = False, show_attendance: bool = True) -> SimpleNamespace:
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


async def _calculate_single_and_batch(
    *,
    student: MagicMock,
    lessons: list[MagicMock],
    attendance_records: list[MagicMock],
    settings: AttestationSettings,
):
    subject_scope = SimpleNamespace(subject_id=None, can_use_legacy_activity_points=False)
    student_calc = StudentScoreCalculator(AsyncMock())
    batch_calc = BatchScoreCalculator(AsyncMock())

    with (
        patch(
            "app.services.attestation.student_score.resolve_attestation_subject_scope",
            new=AsyncMock(return_value=subject_scope),
        ),
        patch(
            "app.services.attestation.student_score.get_student_submission_grade_fallbacks",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "app.services.attestation.batch.resolve_attestation_subject_scope",
            new=AsyncMock(return_value=subject_scope),
        ),
        patch(
            "app.services.attestation.batch.get_submission_grade_fallbacks_batch",
            new=AsyncMock(return_value={student.id: []}),
        ),
        patch(
            "app.services.attestation.batch.load_period_lessons",
            new=AsyncMock(return_value=lessons),
        ),
        patch(
            "app.services.attestation.batch.load_attendance_by_student_for_lessons",
            new=AsyncMock(return_value={student.id: attendance_records}),
        ),
    ):
        student_calc.settings_manager.get_or_create_settings = AsyncMock(return_value=settings)
        student_calc._get_student = AsyncMock(return_value=student)
        student_calc._get_lesson_grades = AsyncMock(return_value=[])
        student_calc._get_attendance = AsyncMock(return_value=attendance_records)
        student_calc._get_activity_points = AsyncMock(return_value=0.0)
        student_calc._get_transfers_in_period = AsyncMock(return_value=[])
        student_calc._get_expected_lessons = AsyncMock(return_value=len(lessons))

        single_result = await student_calc.calculate(
            student_id=student.id,
            group_id=student.group_id,
            attestation_type=settings.attestation_type,
        )

        batch_calc.settings_manager.get_or_create_settings = AsyncMock(return_value=settings)
        batch_calc._get_lessons = AsyncMock(return_value=lessons)
        batch_calc._get_lesson_grades_batch = AsyncMock(return_value={student.id: []})
        batch_calc._get_attendance_batch = AsyncMock(return_value={student.id: attendance_records})
        batch_calc._get_activity_batch = AsyncMock(return_value={student.id: 0.0})
        batch_calc._get_transfers_batch = AsyncMock(return_value={student.id: []})

        batch_results, errors = await batch_calc.calculate_group_batch(
            group_id=student.group_id,
            attestation_type=settings.attestation_type,
            students=[student],
        )

    assert errors == []
    assert len(batch_results) == 1
    return single_result, batch_results[0]


@pytest.mark.asyncio
async def test_attestation_single_and_batch_match_for_mixed_attendance_inputs():
    settings = _make_settings(start=date(2025, 9, 1), end=date(2025, 10, 27))
    student = _make_student(subgroup=1)
    lessons = [
        _make_lesson(lesson_date=date(2025, 9, 1), lesson_number=1),
        _make_lesson(lesson_date=date(2025, 9, 8), lesson_number=1),
        _make_lesson(lesson_date=date(2025, 9, 15), lesson_number=1),
        _make_lesson(lesson_date=date(2025, 9, 22), lesson_number=1),
    ]
    attendance_records = [
        _make_attendance(student_id=student.id, lesson=lessons[0], status=AttendanceStatus.PRESENT),
        _make_attendance(student_id=student.id, lesson=lessons[1], status=AttendanceStatus.LATE),
        _make_attendance(student_id=student.id, lesson=lessons[2], status=AttendanceStatus.EXCUSED),
        _make_attendance(student_id=student.id, lesson=lessons[3], status=AttendanceStatus.ABSENT),
    ]

    single_result, batch_result = await _calculate_single_and_batch(
        student=student,
        lessons=lessons,
        attendance_records=attendance_records,
        settings=settings,
    )

    assert batch_result.breakdown.attendance_score == single_result.breakdown.attendance_score
    assert batch_result.breakdown.attendance_ratio == single_result.breakdown.attendance_ratio
    assert batch_result.breakdown.expected_lessons == single_result.breakdown.expected_lessons
    assert batch_result.breakdown.present_count == 1
    assert batch_result.breakdown.late_count == 1
    assert batch_result.breakdown.excused_count == 1
    assert batch_result.breakdown.absent_count == 1


@pytest.mark.asyncio
async def test_attestation_single_and_batch_keep_all_excused_full_credit_in_sync():
    settings = _make_settings(start=date(2025, 9, 1), end=date(2025, 10, 27))
    student = _make_student()
    lessons = [
        _make_lesson(lesson_date=date(2025, 9, 1), lesson_number=1),
        _make_lesson(lesson_date=date(2025, 9, 8), lesson_number=1),
        _make_lesson(lesson_date=date(2025, 9, 15), lesson_number=1),
    ]
    attendance_records = [
        _make_attendance(student_id=student.id, lesson=lesson, status=AttendanceStatus.EXCUSED)
        for lesson in lessons
    ]

    single_result, batch_result = await _calculate_single_and_batch(
        student=student,
        lessons=lessons,
        attendance_records=attendance_records,
        settings=settings,
    )

    expected_max = settings.get_max_component_points(settings.attendance_weight)
    assert single_result.breakdown.attendance_score == expected_max
    assert batch_result.breakdown.attendance_score == expected_max
    assert single_result.breakdown.attendance_ratio == 1.0
    assert batch_result.breakdown.attendance_ratio == 1.0


@pytest.mark.asyncio
async def test_group_report_attendance_uses_selected_attestation_period(mock_db):
    period_start = date(2025, 9, 1)
    period_end = date(2025, 10, 27)
    settings = _make_settings(start=period_start, end=period_end)
    group_id = uuid4()
    created_by = uuid4()
    student = _make_student()
    student.group_id = group_id
    report = _make_report(group_id=group_id, created_by=created_by)
    collector = ReportDataCollector(mock_db)

    with (
        patch("app.services.reports.group_report_collector.get_group", new=AsyncMock(return_value=SimpleNamespace(code="IT-11", name="ИТ-11", has_subgroups=False))),
        patch("app.services.reports.group_report_collector.get_user", new=AsyncMock(return_value=None)),
        patch("app.services.reports.group_report_collector.get_group_students", new=AsyncMock(return_value=[student])),
        patch("app.services.reports.group_report_collector.get_semester_info", new=AsyncMock(return_value=(False, 35, 20, True))),
        patch("app.services.reports.group_report_collector.get_semester_start_date", new=AsyncMock(return_value=period_start)),
        patch("app.services.reports.group_report_collector.get_group_labs_stats", new=AsyncMock(return_value={})),
        patch("app.services.reports.group_report_collector.process_students", return_value=([], 0, 0, 0)),
        patch("app.services.attestation.service.AttestationService.get_or_create_settings", new=AsyncMock(return_value=settings)),
        patch("app.services.attestation.service.AttestationService.calculate_group_scores_batch", new=AsyncMock(return_value=([], []))),
        patch("app.services.reports.group_report_collector.load_group_attendance_snapshots", new=AsyncMock(return_value=([], {}))) as load_snapshots_mock,
        patch("app.services.reports.group_report_collector.build_group_attendance_stats", return_value={}),
        patch("app.services.reports.group_report_collector.build_attendance_distribution", return_value=AttendanceDistribution()),
        patch(
            "app.services.reports.group_report_collector.build_full_attendance_stats",
            return_value=AttendanceStats(distribution=AttendanceDistribution(), by_subgroup={}, trend=[], average_rate=0.0),
        ),
        patch("app.services.reports.group_report_collector.get_recent_lessons_history", new=AsyncMock(return_value=[])) as history_mock,
        patch("app.services.reports.group_report_collector.get_today_lessons_attendance", new=AsyncMock(return_value=[])) as today_mock,
    ):
        result = await collector.get_group_report_data(report, attestation_type="first")

    assert result.attestation_type == "first"
    assert load_snapshots_mock.await_args.kwargs["period_start"] == period_start
    assert load_snapshots_mock.await_args.kwargs["period_end"] == period_end
    assert history_mock.await_args.kwargs["period_start_date"] == period_start
    assert history_mock.await_args.kwargs["period_end_date"] == period_end
    assert today_mock.await_args.kwargs["period_start_date"] == period_start
    assert today_mock.await_args.kwargs["period_end_date"] == period_end


@pytest.mark.asyncio
async def test_student_detail_attendance_uses_selected_attestation_period(mock_db):
    period_start = date(2025, 9, 1)
    period_end = date(2025, 10, 27)
    settings = _make_settings(start=period_start, end=period_end)
    student = _make_student(subgroup=1)
    report = _make_report(group_id=student.group_id, created_by=uuid4())
    lessons = [
        _make_lesson(lesson_date=date(2025, 9, 1), lesson_number=1),
        _make_lesson(lesson_date=date(2025, 9, 8), lesson_number=1),
    ]
    snapshot = StudentAttendanceSnapshot(
        expected_lessons=2,
        counts=AttendanceCounts(present=1, late=1, excused=0, absent=0),
        statuses_by_lesson_key={
            f"{lessons[0].date}_{lessons[0].lesson_number}": AttendanceStatus.PRESENT,
            f"{lessons[1].date}_{lessons[1].lesson_number}": AttendanceStatus.LATE,
        },
    )

    with (
        patch("app.services.reports.student_detail_collector.get_user", new=AsyncMock(return_value=student)),
        patch("app.services.reports.student_detail_collector.get_group", new=AsyncMock(return_value=SimpleNamespace(code="IT-11"))),
        patch("app.services.reports.student_detail_collector.get_semester_info", new=AsyncMock(return_value=(False, 35, 20, True))),
        patch("app.services.attestation.service.AttestationService.get_or_create_settings", new=AsyncMock(return_value=settings)),
        patch(
            "app.services.attestation.service.AttestationService.calculate_student_score",
            new=AsyncMock(return_value=SimpleNamespace(is_passing=True, max_points=35, min_passing_points=20)),
        ),
        patch(
            "app.services.reports.student_detail_collector.load_group_attendance_snapshots",
            new=AsyncMock(return_value=(lessons, {student.id: snapshot})),
        ) as load_snapshots_mock,
    ):
        result = await collect_student_report_data(
            db=mock_db,
            report=report,
            student_id=student.id,
            attestation_type="first",
        )

    assert result is not None
    assert result.attendance_rate == 75.0
    assert result.total_lessons == 2
    assert len(result.attendance_history or []) == 2
    assert load_snapshots_mock.await_args.kwargs["period_start"] == period_start
    assert load_snapshots_mock.await_args.kwargs["period_end"] == period_end


@pytest.mark.asyncio
async def test_export_collect_attendance_reuses_report_snapshot_derivation(mock_db):
    group_id = uuid4()
    student = _make_student(subgroup=1)
    student.group_id = group_id
    lessons = [
        _make_lesson(lesson_date=date(2025, 9, 1), lesson_number=1),
        _make_lesson(lesson_date=date(2025, 9, 8), lesson_number=1),
        _make_lesson(lesson_date=date(2025, 9, 15), lesson_number=1),
        _make_lesson(lesson_date=date(2025, 9, 22), lesson_number=1, subgroup=1),
    ]
    attendance_records = [
        _make_attendance(student_id=student.id, lesson=lessons[0], status=AttendanceStatus.PRESENT),
        _make_attendance(student_id=student.id, lesson=lessons[1], status=AttendanceStatus.LATE),
        _make_attendance(student_id=student.id, lesson=lessons[2], status=AttendanceStatus.EXCUSED),
    ]
    expected_snapshots = build_student_attendance_snapshots(
        students=[student],
        lessons=lessons,
        attendance_records=attendance_records,
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = attendance_records
    mock_db.execute.return_value = mock_result

    with patch(
        "app.services.export.attendance_helpers.load_attendance_by_student_for_lessons",
        new=AsyncMock(return_value={student.id: attendance_records}),
    ):
        rows = await collect_attendance_rows(
            mock_db,
            group_id=group_id,
            lessons=lessons,
            students=[student],
        )

    assert len(rows) == 1
    row = rows[0]
    snapshot = expected_snapshots[student.id]
    assert row.attendance_rate == snapshot.report_rate()
    assert row.stats == {
        "present_count": snapshot.counts.present,
        "absent_count": snapshot.counts.absent,
        "late_count": snapshot.counts.late,
        "excused_count": snapshot.counts.excused,
        "total": snapshot.expected_lessons,
    }
