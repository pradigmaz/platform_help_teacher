"""Тесты нормализации прогресса лабораторных."""

import sys
from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

sys.path.insert(0, "/app")

from app.crud import crud_lesson_grade
from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.lab import Lab
from app.models.lesson_grade import LessonGrade
from app.models.submission import Submission, SubmissionStatus
from app.services.attendance_slots import matches_attendance_slot
from app.services.attestation.lab_calculator import LabScoreCalculator
from app.services.attestation.student_score import StudentScoreCalculator
from app.services.student_lab_service import StudentLabService


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


def _build_grade(*, grade_value: int, work_number: int, created_at: datetime, updated_at: datetime | None = None):
    grade = MagicMock(spec=LessonGrade)
    grade.id = uuid4()
    grade.lesson_id = uuid4()
    grade.student_id = uuid4()
    grade.work_number = work_number
    grade.grade = grade_value
    grade.comment = None
    grade.created_at = created_at
    grade.updated_at = updated_at or created_at
    return grade


class TestLabProgressNormalization:
    def test_lab_calculator_counts_only_grades_above_two(self):
        calculator = LabScoreCalculator()
        now = datetime.now(UTC)
        lesson_grades = [
            _build_grade(grade_value=2, work_number=1, created_at=now),
            _build_grade(grade_value=4, work_number=2, created_at=now + timedelta(minutes=1)),
        ]

        result = calculator.calculate(
            lesson_grades,
            _build_settings(),
            transfer_grades=[
                {"work_number": 3, "grade": 2},
                {"work_number": 4, "grade": 5},
            ],
        )

        assert result.labs_count == 2
        assert result.needs_rework == 2

    @pytest.mark.asyncio
    async def test_student_score_dedupes_by_subject_and_latest_row(self):
        subject_a = uuid4()
        subject_b = uuid4()
        student_id = uuid4()
        group_id = uuid4()
        now = datetime.now(UTC)

        older = _build_grade(grade_value=5, work_number=4, created_at=now)
        newer = _build_grade(
            grade_value=5,
            work_number=4,
            created_at=now - timedelta(hours=1),
            updated_at=now + timedelta(hours=1),
        )
        other_subject = _build_grade(grade_value=3, work_number=4, created_at=now + timedelta(minutes=5))

        mock_result = MagicMock()
        mock_result.all.return_value = [(older, subject_a), (newer, subject_a), (other_subject, subject_b)]
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        calculator = StudentScoreCalculator(mock_db)
        grades = await calculator._get_lesson_grades(student_id, group_id, _build_settings())

        assert grades == [newer, other_subject]

    @pytest.mark.asyncio
    async def test_student_score_handles_sqlalchemy_row_like_results(self):
        subject_id = uuid4()
        student_id = uuid4()
        group_id = uuid4()
        now = datetime.now(UTC)

        older = _build_grade(grade_value=4, work_number=2, created_at=now)
        newer = _build_grade(
            grade_value=5,
            work_number=2,
            created_at=now - timedelta(minutes=1),
            updated_at=now + timedelta(minutes=1),
        )

        class FakeRow:
            def __init__(self, grade: LessonGrade, subject: UUID):
                self._items = (grade, subject)

            def __iter__(self):
                return iter(self._items)

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.all.return_value = [FakeRow(older, subject_id), FakeRow(newer, subject_id)]
        mock_result.scalars.return_value = mock_scalars
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        calculator = StudentScoreCalculator(mock_db)
        grades = await calculator._get_lesson_grades(student_id, group_id, _build_settings())

        assert grades == [newer]

    @pytest.mark.asyncio
    async def test_student_lab_service_dedupes_journal_grades_per_subject(self, mock_db: AsyncMock):
        subject_id = uuid4()
        now = datetime.now(UTC)
        older = _build_grade(grade_value=4, work_number=2, created_at=now)
        newer = _build_grade(
            grade_value=4,
            work_number=2,
            created_at=now - timedelta(minutes=5),
            updated_at=now + timedelta(minutes=5),
        )

        mock_result = MagicMock()
        mock_result.all.return_value = [(older, subject_id), (newer, subject_id)]
        mock_db.execute.return_value = mock_result

        service = StudentLabService()
        grades_by_subject = await service.get_user_journal_grades_by_subject(mock_db, uuid4())

        assert grades_by_subject[subject_id][2] is newer

    @pytest.mark.asyncio
    async def test_check_lab_availability_uses_journal_acceptance(self, mock_db: AsyncMock):
        service = StudentLabService()
        user_id = uuid4()
        subject_id = uuid4()
        current_lab = Lab(id=uuid4(), number=2, title="Lab 2", subject_id=subject_id, is_sequential=True)
        previous_lab = Lab(id=uuid4(), number=1, title="Lab 1", subject_id=subject_id, is_sequential=True)
        previous_journal_grade = _build_grade(
            grade_value=4,
            work_number=1,
            created_at=datetime.now(UTC),
        )

        previous_lab_result = MagicMock()
        previous_lab_result.scalar_one_or_none.return_value = previous_lab
        previous_submission_result = MagicMock()
        previous_submission_result.scalar_one_or_none.return_value = None
        mock_db.execute.side_effect = [previous_lab_result, previous_submission_result]
        service.get_user_journal_grades_by_subject = AsyncMock(return_value={subject_id: {1: previous_journal_grade}})

        is_available = await service.check_lab_availability(mock_db, user_id, current_lab)

        assert is_available is True

    @pytest.mark.asyncio
    async def test_mark_ready_allows_stale_submission_when_journal_grade_is_two(self, mock_db: AsyncMock):
        service = StudentLabService()
        user_id = uuid4()
        lab_id = uuid4()
        subject_id = uuid4()
        stale_submission = Submission(
            id=uuid4(),
            user_id=user_id,
            lab_id=lab_id,
            status=SubmissionStatus.ACCEPTED,
            is_manual=True,
        )
        lab = Lab(id=lab_id, number=3, title="Lab 3", subject_id=subject_id, is_sequential=True)
        rework_grade = _build_grade(grade_value=2, work_number=3, created_at=datetime.now(UTC))

        service.get_user_submission_for_lab = AsyncMock(return_value=stale_submission)
        service.get_lab_by_id = AsyncMock(return_value=lab)
        service.get_user_journal_grades_by_subject = AsyncMock(return_value={subject_id: {3: rework_grade}})

        result = await service.mark_ready(mock_db, user_id, lab_id, variant_number=1)

        assert result.status == SubmissionStatus.READY
        assert result.variant_number == 1
        mock_db.commit.assert_awaited_once()

    def test_attendance_slot_matching_uses_lesson_id_or_slot_tuple(self):
        lesson_id = uuid4()
        matching_by_lesson = MagicMock()
        matching_by_lesson.lesson_id = lesson_id
        matching_by_lesson.date = date(2025, 9, 1)
        matching_by_lesson.lesson_number = 1

        matching_legacy = MagicMock()
        matching_legacy.lesson_id = None
        matching_legacy.date = date(2025, 9, 1)
        matching_legacy.lesson_number = 2

        foreign_parallel = MagicMock()
        foreign_parallel.lesson_id = None
        foreign_parallel.date = date(2025, 9, 1)
        foreign_parallel.lesson_number = 3

        lesson_ids = {lesson_id}
        legacy_slots = {(date(2025, 9, 1), 2)}

        assert matches_attendance_slot(matching_by_lesson, lesson_ids=lesson_ids, legacy_slots=legacy_slots) is True
        assert matches_attendance_slot(matching_legacy, lesson_ids=lesson_ids, legacy_slots=legacy_slots) is True
        assert matches_attendance_slot(foreign_parallel, lesson_ids=lesson_ids, legacy_slots=legacy_slots) is False

    @pytest.mark.asyncio
    async def test_update_lesson_grade_merges_duplicate_work_number(self, mock_db: AsyncMock, monkeypatch: pytest.MonkeyPatch):
        lesson_id = uuid4()
        grade_id = uuid4()
        current_grade = _build_grade(
            grade_value=3,
            work_number=3,
            created_at=datetime.now(UTC),
        )
        current_grade.id = grade_id
        current_grade.lesson_id = lesson_id
        current_grade.comment = "old"
        current_grade.lesson = MagicMock(group_id=uuid4(), subject_id=uuid4())

        existing_grade = _build_grade(
            grade_value=5,
            work_number=4,
            created_at=datetime.now(UTC) + timedelta(minutes=1),
        )
        existing_grade.lesson_id = uuid4()
        existing_grade.comment = "existing"

        get_grade_result = MagicMock()
        get_grade_result.scalar_one_or_none.return_value = current_grade
        mock_db.execute.return_value = get_grade_result

        async def _fake_get_student_grade_by_work(*args, **kwargs):
            return existing_grade

        monkeypatch.setattr(crud_lesson_grade, "get_student_grade_by_work", _fake_get_student_grade_by_work)

        updated = await crud_lesson_grade.update_lesson_grade(
            mock_db,
            grade_id=grade_id,
            grade=4,
            work_number=4,
            comment="merged",
        )

        assert updated is existing_grade
        assert existing_grade.lesson_id == lesson_id
        assert existing_grade.work_number == 4
        assert existing_grade.grade == 4
        assert existing_grade.comment == "merged"
        mock_db.delete.assert_awaited_once_with(current_grade)
        mock_db.commit.assert_awaited_once()
        mock_db.refresh.assert_awaited_once_with(existing_grade)
