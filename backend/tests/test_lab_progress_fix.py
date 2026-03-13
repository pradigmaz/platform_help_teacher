from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.crud import crud_lesson_grade
from app.models.attestation_settings import AttestationSettings, AttestationType
from app.models.lesson_grade import LessonGrade
from app.models.submission import Submission, SubmissionStatus
from app.services.attestation.lab_calculator import LabScoreCalculator
from app.services.attestation.lab_progress import (
    dedupe_lesson_grade_rows,
    dedupe_submission_lab_grades,
    dedupe_transfer_lab_grades,
)
from app.services.student_lab_service import _GradeRow, resolve_lab_acceptance


def make_grade(*, work_number: int, grade: int, created_at: datetime, student_id=None, lesson_id=None) -> LessonGrade:
    lesson_grade = LessonGrade(
        id=uuid4(),
        lesson_id=lesson_id or uuid4(),
        student_id=student_id or uuid4(),
        work_number=work_number,
        grade=grade,
    )
    lesson_grade.created_at = created_at
    lesson_grade.updated_at = created_at
    return lesson_grade


class TestLabProgressNormalization:
    def test_dedupe_lesson_grade_rows_keeps_best_and_latest(self):
        subject_id = uuid4()
        student_id = uuid4()
        now = datetime.now(UTC)

        older = make_grade(work_number=4, grade=4, created_at=now - timedelta(minutes=5), student_id=student_id)
        better = make_grade(work_number=4, grade=5, created_at=now - timedelta(minutes=1), student_id=student_id)
        latest_same_grade = make_grade(work_number=2, grade=3, created_at=now, student_id=student_id)
        earlier_same_grade = make_grade(
            work_number=2, grade=3, created_at=now - timedelta(minutes=10), student_id=student_id
        )

        deduped = dedupe_lesson_grade_rows(
            [
                (older, subject_id),
                (better, subject_id),
                (earlier_same_grade, subject_id),
                (latest_same_grade, subject_id),
            ]
        )

        assert len(deduped) == 2
        assert {grade.work_number for grade in deduped} == {2, 4}
        assert next(grade for grade in deduped if grade.work_number == 4).id == better.id
        assert next(grade for grade in deduped if grade.work_number == 2).id == latest_same_grade.id

    def test_dedupe_transfer_lab_grades_keeps_best_and_latest_per_subject(self):
        subject_a = str(uuid4())
        subject_b = str(uuid4())

        deduped = dedupe_transfer_lab_grades(
            [
                {"subject_id": subject_a, "work_number": 4, "grade": 3, "lesson_id": "old"},
                {"subject_id": subject_a, "work_number": 4, "grade": 4, "lesson_id": "better"},
                {"subject_id": subject_b, "work_number": 4, "grade": 5, "lesson_id": "other-subject"},
                {"subject_id": subject_a, "work_number": 2, "grade": 5, "lesson_id": "first"},
                {"subject_id": subject_a, "work_number": 2, "grade": 5, "lesson_id": "latest"},
            ]
        )

        by_key = {(grade["subject_id"], grade["work_number"]): grade for grade in deduped}
        assert by_key[(subject_a, 4)]["lesson_id"] == "better"
        assert by_key[(subject_b, 4)]["lesson_id"] == "other-subject"
        assert by_key[(subject_a, 2)]["lesson_id"] == "latest"

    def test_lab_calculator_counts_only_grades_above_two_and_dedupes_transfer(self):
        now = datetime.now(UTC)
        calculator = LabScoreCalculator()
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            labs_count_first=5,
            grade_4_coef=0.7,
            grade_3_coef=0.4,
        )

        grade_rework = make_grade(work_number=1, grade=2, created_at=now)
        grade_rework.lab_subject_id = uuid4()
        grade_current = make_grade(work_number=2, grade=3, created_at=now)
        grade_current.lab_subject_id = uuid4()
        grade_other_subject = make_grade(work_number=2, grade=5, created_at=now)
        grade_other_subject.lab_subject_id = uuid4()

        result = calculator.calculate(
            lesson_grades=[grade_rework, grade_current, grade_other_subject],
            settings=settings,
            transfer_grades=[
                {
                    "subject_id": str(grade_current.lab_subject_id),
                    "work_number": 2,
                    "grade": 5,
                    "lesson_id": "upgraded",
                },
                {"subject_id": str(uuid4()), "work_number": 5, "grade": 2},
            ],
        )

        assert result.labs_count == 2
        assert result.needs_rework == 2
        assert len(result.details) == 4
        assert any(
            detail["subject_id"] == str(grade_current.lab_subject_id)
            and detail["work_number"] == 2
            and detail["grade"] == 5
            for detail in result.details
        )

    def test_lab_calculator_uses_submission_when_journal_grade_missing(self):
        now = datetime.now(UTC)
        calculator = LabScoreCalculator()
        settings = AttestationSettings(
            attestation_type=AttestationType.FIRST,
            labs_weight=70.0,
            attendance_weight=20.0,
            activity_reserve=10.0,
            labs_count_first=4,
            grade_4_coef=0.7,
            grade_3_coef=0.4,
        )

        journal_grade = make_grade(work_number=1, grade=4, created_at=now)
        journal_grade.lab_subject_id = uuid4()
        subject_id = str(uuid4())

        result = calculator.calculate(
            lesson_grades=[journal_grade],
            settings=settings,
            submission_grades=[
                {"subject_id": str(journal_grade.lab_subject_id), "work_number": 1, "grade": 5},
                {"subject_id": subject_id, "work_number": 3, "grade": 5, "lesson_id": str(uuid4())},
            ],
        )

        details_by_key = {(detail["subject_id"], detail["work_number"]): detail for detail in result.details}

        assert details_by_key[(str(journal_grade.lab_subject_id), 1)]["grade"] == 4
        assert details_by_key[(str(journal_grade.lab_subject_id), 1)]["source"] == "journal"
        assert details_by_key[(subject_id, 3)]["grade"] == 5
        assert details_by_key[(subject_id, 3)]["source"] == "submission"
        assert result.labs_count == 2

    def test_dedupe_submission_lab_grades_keeps_best_latest_submission(self):
        subject_id = uuid4()
        now = datetime.now(UTC)

        weaker = Submission(
            id=uuid4(),
            user_id=uuid4(),
            lab_id=uuid4(),
            lesson_id=uuid4(),
            status=SubmissionStatus.ACCEPTED,
            grade=4,
            is_manual=True,
        )
        weaker.created_at = now
        weaker.accepted_at = now

        better = Submission(
            id=uuid4(),
            user_id=weaker.user_id,
            lab_id=uuid4(),
            lesson_id=uuid4(),
            status=SubmissionStatus.ACCEPTED,
            grade=5,
            is_manual=True,
        )
        better.created_at = now + timedelta(minutes=1)
        better.accepted_at = now + timedelta(minutes=1)

        deduped = dedupe_submission_lab_grades(
            [
                (weaker, subject_id, 3),
                (better, subject_id, 3),
            ]
        )

        assert deduped == [
            {
                "submission_id": str(better.id),
                "lesson_id": str(better.lesson_id),
                "subject_id": str(subject_id),
                "work_number": 3,
                "grade": 5,
                "accepted_at": better.accepted_at.isoformat(),
                "created_at": better.created_at.isoformat(),
            }
        ]

    def test_resolve_lab_acceptance_prefers_journal_even_for_grade_two(self):
        submission = Submission(
            id=uuid4(),
            user_id=uuid4(),
            lab_id=uuid4(),
            status=SubmissionStatus.ACCEPTED,
            is_manual=True,
        )
        journal_grade = _GradeRow(
            id=str(uuid4()),
            lesson_id=str(uuid4()),
            student_id=str(uuid4()),
            work_number=4,
            grade=2,
            comment=None,
            created_at=datetime.now(UTC),
        )

        is_accepted, journal_grade_value, acceptance_source = resolve_lab_acceptance(submission, journal_grade)

        assert is_accepted is False
        assert journal_grade_value == 2
        assert acceptance_source is None


class TestLessonGradePatchMerge:
    @pytest.mark.asyncio
    async def test_update_lesson_grade_merges_cross_lesson_duplicate(self, mock_db: AsyncMock, monkeypatch):
        student_id = uuid4()
        group_id = uuid4()
        subject_id = uuid4()
        source_grade = make_grade(
            work_number=3,
            grade=3,
            created_at=datetime.now(UTC),
            student_id=student_id,
            lesson_id=uuid4(),
        )
        source_grade.comment = "source-comment"
        source_grade.lesson = MagicMock(group_id=group_id, subject_id=subject_id)

        existing_grade = make_grade(
            work_number=4,
            grade=5,
            created_at=datetime.now(UTC),
            student_id=student_id,
            lesson_id=uuid4(),
        )
        existing_grade.comment = "existing-comment"

        monkeypatch.setattr(crud_lesson_grade, "get_student_grade_by_work", AsyncMock(return_value=existing_grade))
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = source_grade
        mock_db.execute.return_value = mock_result

        merged = await crud_lesson_grade.update_lesson_grade(
            mock_db,
            grade_id=source_grade.id,
            work_number=4,
        )

        assert merged is existing_grade
        assert existing_grade.lesson_id == source_grade.lesson_id
        assert existing_grade.grade == source_grade.grade
        assert existing_grade.comment == source_grade.comment
        mock_db.delete.assert_awaited_once_with(source_grade)
        mock_db.commit.assert_awaited_once()
        mock_db.refresh.assert_awaited_once_with(existing_grade)
        crud_lesson_grade.get_student_grade_by_work.assert_awaited_once_with(
            mock_db,
            student_id,
            4,
            group_id=group_id,
            subject_id=subject_id,
            exclude_grade_id=source_grade.id,
        )
