"""Contract checks for attendance loading during attestation calculations."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.attestation_settings import AttestationSettings, AttestationType


class TestCancelledLessonFilteringContract:
    @pytest.mark.asyncio
    async def test_get_attendance_should_exclude_cancelled_lessons(self):
        from app.models.lesson import Lesson
        from app.services.attestation.student_score import StudentScoreCalculator

        group_id = uuid4()
        student_id = uuid4()
        cancelled_date = date(2025, 10, 8)
        normal_date = date(2025, 10, 1)

        normal_lesson = MagicMock(spec=Lesson)
        normal_lesson.date = normal_date
        normal_lesson.is_cancelled = False
        normal_lesson.subgroup = None

        cancelled_lesson = MagicMock(spec=Lesson)
        cancelled_lesson.date = cancelled_date
        cancelled_lesson.is_cancelled = True
        cancelled_lesson.subgroup = None

        mock_db = AsyncMock()
        lessons_scalars = MagicMock()
        lessons_scalars.all.return_value = [normal_lesson, cancelled_lesson]
        lessons_result = MagicMock()
        lessons_result.scalars.return_value = lessons_scalars
        att_scalars = MagicMock()
        att_scalars.all.return_value = []
        att_result = MagicMock()
        att_result.scalars.return_value = att_scalars
        mock_db.execute.side_effect = [lessons_result, att_result]

        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            semester_start_date=date(2025, 9, 1),
        )

        calculator = StudentScoreCalculator(mock_db)
        await calculator._get_attendance(student_id, group_id, None, settings)

        query_lower = str(mock_db.execute.call_args_list[0][0][0]).lower()
        where_idx = query_lower.find("where")
        where_clause = query_lower[where_idx:] if where_idx != -1 else ""

        assert "is_cancelled" in where_clause, (
            f"Counterexample: WHERE clause запроса к занятиям не содержит фильтр is_cancelled: {where_clause}"
        )

    @pytest.mark.asyncio
    async def test_cancelled_lesson_date_not_in_attendance_query(self):
        from app.models.lesson import Lesson
        from app.services.attestation.student_score import StudentScoreCalculator

        group_id = uuid4()
        student_id = uuid4()
        cancelled_date = date(2025, 10, 8)
        normal_date = date(2025, 10, 1)

        normal_lesson = MagicMock(spec=Lesson)
        normal_lesson.date = normal_date
        normal_lesson.is_cancelled = False
        normal_lesson.subgroup = None

        cancelled_lesson = MagicMock(spec=Lesson)
        cancelled_lesson.date = cancelled_date
        cancelled_lesson.is_cancelled = True
        cancelled_lesson.subgroup = None

        mock_db = AsyncMock()
        lessons_scalars = MagicMock()
        lessons_scalars.all.return_value = [normal_lesson, cancelled_lesson]
        lessons_result = MagicMock()
        lessons_result.scalars.return_value = lessons_scalars
        att_scalars = MagicMock()
        att_scalars.all.return_value = []
        att_result = MagicMock()
        att_result.scalars.return_value = att_scalars
        mock_db.execute.side_effect = [lessons_result, att_result]

        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            semester_start_date=date(2025, 9, 1),
        )

        calculator = StudentScoreCalculator(mock_db)
        await calculator._get_attendance(student_id, group_id, None, settings)

        att_query_str = str(mock_db.execute.call_args_list[1][0][0])
        assert str(cancelled_date) not in att_query_str, (
            f"Counterexample: дата отменённого занятия {cancelled_date} присутствует в attendance query: {att_query_str}"
        )


class TestAttendanceBatchPeriodContract:
    @pytest.mark.asyncio
    async def test_get_attendance_batch_should_filter_by_period(self):
        from app.models.lesson import Lesson, LessonType
        from app.services.attendance_period import load_attendance_by_student_for_lessons

        group_id = uuid4()
        student_ids = [uuid4(), uuid4()]
        lesson = Lesson(
            id=uuid4(),
            group_id=group_id,
            subject_id=uuid4(),
            date=date(2025, 9, 10),
            lesson_number=2,
            lesson_type=LessonType.LAB,
        )

        mock_db = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        await load_attendance_by_student_for_lessons(
            mock_db,
            group_id=group_id,
            student_ids=student_ids,
            lessons=[lesson],
        )

        executed_query = str(mock_db.execute.call_args[0][0]).lower()
        assert "attendance.lesson_id" in executed_query, "Expected slot-filter by attendance.lesson_id"
        assert "attendance.date >=" not in executed_query
        assert "attendance.date <=" not in executed_query
