from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.lab import Lab
from app.models.lesson import Lesson, LessonType
from app.models.submission import Submission, SubmissionStatus
from app.services.attestation.batch import BatchScoreCalculator
from app.services.attestation.submission_fallbacks import get_student_submission_grade_fallbacks
from app.services.submission_service import SubmissionService, journal_grade_service


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


class TestSubmissionAcceptanceContext:
    @pytest.mark.asyncio
    async def test_accept_persists_resolved_lesson_context(self, monkeypatch: pytest.MonkeyPatch):
        submission = Submission(
            id=uuid4(),
            user_id=uuid4(),
            lab_id=uuid4(),
            status=SubmissionStatus.READY,
            is_manual=True,
            history=[],
        )
        lesson = Lesson(
            id=uuid4(),
            group_id=uuid4(),
            subject_id=uuid4(),
            date=date(2025, 9, 10),
            lesson_number=2,
            lesson_type=LessonType.LAB,
        )
        lab = Lab(
            id=submission.lab_id,
            number=4,
            title="Lab 4",
            subject_id=lesson.subject_id,
            is_published=True,
        )

        mock_db = AsyncMock()
        monkeypatch.setattr(
            SubmissionService,
            "_resolve_acceptance_context",
            AsyncMock(return_value=(lab, lesson)),
        )
        monkeypatch.setattr(journal_grade_service, "write_grade", AsyncMock())

        service = SubmissionService()
        result = await service.accept(mock_db, submission, grade=5, comment="ok", accepted_by=uuid4())

        assert result["status"] == "accepted"
        assert submission.lesson_id == lesson.id
        assert submission.lesson_date == lesson.date
        assert submission.lesson_number == lesson.lesson_number
        journal_grade_service.write_grade.assert_awaited_once()
        mock_db.commit.assert_awaited_once()


class TestSubmissionFallbackQueries:
    @pytest.mark.asyncio
    async def test_student_fallback_query_uses_lesson_subject(self):
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        await get_student_submission_grade_fallbacks(mock_db, uuid4(), uuid4(), _build_settings())

        query = str(mock_db.execute.call_args[0][0]).lower()

        assert "join lessons" in query
        assert "lessons.subject_id" in query
        assert "labs.subject_id is not null" not in query

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
