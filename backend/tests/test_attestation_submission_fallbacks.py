from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.lesson import Lesson, LessonType
from app.services.attestation.batch import BatchScoreCalculator
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


class TestSubmissionFallbackQueries:
    @pytest.mark.asyncio
    async def test_student_fallback_query_supports_legacy_submission_context(self):
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        await get_student_submission_grade_fallbacks(mock_db, uuid4(), uuid4(), _build_settings())

        query = str(mock_db.execute.call_args[0][0]).lower()

        assert "left outer join lessons" in query
        assert "coalesce(lessons.subject_id, labs.subject_id)" in query
        assert "coalesce(lessons.date, submissions.lesson_date" in query
        assert "submissions.lesson_id is null" in query
        assert "lessons.is_cancelled is false" in query

    @pytest.mark.asyncio
    async def test_batch_attendance_query_uses_slot_filter_instead_of_date_bounds(self):
        group_id = uuid4()
        student_id = uuid4()
        lesson = Lesson(
            id=uuid4(),
            group_id=group_id,
            subject_id=uuid4(),
            date=date(2025, 9, 10),
            lesson_number=3,
            lesson_type=LessonType.LAB,
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        calculator = BatchScoreCalculator(mock_db)
        await calculator._get_attendance_batch(group_id, [student_id], _build_settings(), lessons=[lesson])

        query = str(mock_db.execute.call_args[0][0]).lower()

        assert "attendance.lesson_id" in query
        assert "attendance.date >=" not in query
        assert "attendance.date <=" not in query
