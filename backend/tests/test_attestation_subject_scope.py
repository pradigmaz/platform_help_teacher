from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.student_transfer import StudentTransfer
from app.services.attestation.student_score import StudentScoreCalculator
from app.services.attestation.subject_scope import (
    AttestationSubjectScope,
    merge_transfer_attendance,
    resolve_attestation_subject_scope,
)
from app.services.attestation.submission_fallbacks import get_student_submission_grade_fallbacks


def _build_settings() -> AttestationSettings:
    return AttestationSettings(
        attestation_type=AttestationType.FIRST,
        labs_weight=70.0,
        attendance_weight=20.0,
        activity_reserve=10.0,
        labs_count_first=4,
        labs_count_second=0,
        semester_start_date=date(2025, 9, 1),
    )


class TestAttestationSubjectScope:
    @pytest.mark.asyncio
    async def test_list_group_subject_ids_prefers_offerings_over_period_lessons(self):
        subject_id = uuid4()
        mock_db = AsyncMock()

        with patch(
            "app.services.attestation.subject_scope.list_group_subject_ids_for_current_semester",
            new=AsyncMock(return_value=(subject_id,)),
        ):
            scope = await resolve_attestation_subject_scope(mock_db, uuid4(), _build_settings())

        assert scope.subject_id == subject_id
        assert mock_db.execute.await_count == 0

    @pytest.mark.asyncio
    async def test_resolve_requires_subject_when_period_has_multiple_disciplines(self):
        mock_db = AsyncMock()

        with (
            patch(
                "app.services.attestation.subject_scope.list_group_subject_ids_for_current_semester",
                new=AsyncMock(return_value=(uuid4(), uuid4())),
            ),
            pytest.raises(ValueError, match="нужно выбрать предмет"),
        ):
            await resolve_attestation_subject_scope(mock_db, uuid4(), _build_settings())

    @pytest.mark.asyncio
    async def test_resolve_autoselects_single_subject(self):
        subject_id = uuid4()
        mock_db = AsyncMock()

        with patch(
            "app.services.attestation.subject_scope.list_group_subject_ids_for_current_semester",
            new=AsyncMock(return_value=(subject_id,)),
        ):
            scope = await resolve_attestation_subject_scope(mock_db, uuid4(), _build_settings())

        assert scope.subject_id == subject_id
        assert scope.can_use_legacy_activity_points is True


class TestSubjectAwareActivityQueries:
    @pytest.mark.asyncio
    async def test_activity_query_keeps_legacy_nulls_in_explicit_multi_subject_scope(self):
        mock_result = MagicMock()
        mock_result.scalar.return_value = 7.0
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        calculator = StudentScoreCalculator(mock_db)
        subject_id = uuid4()
        scope = AttestationSubjectScope(
            subject_id=subject_id,
            period_subject_ids=(subject_id, uuid4()),
            allow_legacy_unscoped=True,
        )

        await calculator._get_activity_points(uuid4(), AttestationType.FIRST, scope)

        query = str(mock_db.execute.call_args[0][0]).lower()
        assert "activities.subject_id" in query
        assert "activities.subject_id is null" in query

    @pytest.mark.asyncio
    async def test_activity_query_keeps_legacy_nulls_in_single_subject_scope(self):
        mock_result = MagicMock()
        mock_result.scalar.return_value = 9.0
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        calculator = StudentScoreCalculator(mock_db)
        subject_id = uuid4()
        scope = AttestationSubjectScope(
            subject_id=subject_id,
            period_subject_ids=(subject_id,),
            allow_legacy_unscoped=True,
        )

        await calculator._get_activity_points(uuid4(), AttestationType.FIRST, scope)

        query = str(mock_db.execute.call_args[0][0]).lower()
        assert "activities.subject_id" in query
        assert "activities.subject_id is null" in query


class TestSubjectAwareFallbacks:
    @pytest.mark.asyncio
    async def test_submission_fallback_query_respects_subject_and_lab_types(self):
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        subject_id = uuid4()
        await get_student_submission_grade_fallbacks(mock_db, uuid4(), uuid4(), _build_settings(), subject_id=subject_id)

        query = str(mock_db.execute.call_args[0][0]).lower()
        assert "coalesce(lessons.subject_id, labs.subject_id)" in query
        assert "lessons.lesson_type in" in query
        assert "coalesce(lessons.subject_id, labs.subject_id) =" in query

    def test_transfer_attendance_keeps_legacy_snapshot_for_explicit_subject(self):
        first_subject_id = uuid4()
        transfer = StudentTransfer(
            student_id=uuid4(),
            transfer_date=date(2025, 9, 10),
            attestation_type=AttestationType.FIRST,
            attendance_data={"total_lessons": 5, "present": 4, "late": 1, "excused": 0, "absent": 0},
            lab_grades_data=[
                {"subject_id": str(first_subject_id), "work_number": 1, "grade": 5},
                {"subject_id": str(uuid4()), "work_number": 1, "grade": 5},
            ],
            activity_points=3.0,
        )
        scope = AttestationSubjectScope(
            subject_id=first_subject_id,
            period_subject_ids=(first_subject_id, uuid4()),
            allow_legacy_unscoped=True,
        )

        assert merge_transfer_attendance([transfer], scope) == {
            "total_lessons": 5,
            "present": 4,
            "late": 1,
            "excused": 0,
            "absent": 0,
        }
