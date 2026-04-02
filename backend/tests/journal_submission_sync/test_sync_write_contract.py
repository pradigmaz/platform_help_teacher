"""Contract tests for the main journal -> submission write path."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Group, Lab, Lesson, SubmissionStatus, User
from app.models.schedule import LessonType
from app.services.submission_journal_sync import journal_sync

from .conftest import make_submission, scalar_result


class TestSyncFromJournalWriteContract:
    @pytest.mark.asyncio
    async def test_create_submission_from_journal_grade(
        self,
        mock_db,
        sample_student: User,
        sample_lab: Lab,
        sample_lesson: Lesson,
        sample_teacher: User,
    ):
        async def mock_find_published_lab(db, subject_id, work_number):
            if subject_id == sample_lesson.subject_id and work_number == 1:
                return sample_lab
            return None

        mock_db.execute.return_value = scalar_result(None)
        original_find = journal_sync.find_published_lab
        journal_sync.find_published_lab = mock_find_published_lab
        try:
            submission = await journal_sync.sync_from_journal(
                mock_db,
                sample_student.id,
                sample_lesson,
                work_number=1,
                grade=5,
                comment="Отлично выполнено",
                created_by=sample_teacher.id,
            )
        finally:
            journal_sync.find_published_lab = original_find

        assert submission is not None
        assert submission.user_id == sample_student.id
        assert submission.lab_id == sample_lab.id
        assert submission.is_manual is True
        assert submission.status == SubmissionStatus.ACCEPTED
        assert submission.grade == 5
        assert submission.feedback == "Отлично выполнено"
        assert submission.accepted_at is not None
        assert submission.lesson_id == sample_lesson.id
        assert submission.lesson_date == sample_lesson.date
        assert submission.lesson_number == sample_lesson.lesson_number
        assert len(submission.history) == 1
        assert submission.history[0]["action"] == "created_from_journal"
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_existing_submission_grade(
        self,
        mock_db,
        sample_student: User,
        sample_lab: Lab,
        sample_lesson: Lesson,
        sample_teacher: User,
    ):
        existing_submission = make_submission(
            user_id=sample_student.id,
            lab_id=sample_lab.id,
            status=SubmissionStatus.READY,
            history=[{"action": "ready", "at": datetime.now(timezone.utc).isoformat()}],
        )

        async def mock_find_published_lab(db, subject_id, work_number):
            return sample_lab

        mock_db.execute.return_value = scalar_result(existing_submission)
        original_find = journal_sync.find_published_lab
        journal_sync.find_published_lab = mock_find_published_lab
        try:
            submission = await journal_sync.sync_from_journal(
                mock_db,
                sample_student.id,
                sample_lesson,
                work_number=1,
                grade=4,
                comment="Хорошо",
                created_by=sample_teacher.id,
            )
        finally:
            journal_sync.find_published_lab = original_find

        assert submission is not None
        assert submission.id == existing_submission.id
        assert submission.grade == 4
        assert submission.status == SubmissionStatus.ACCEPTED
        assert submission.feedback == "Хорошо"
        assert submission.accepted_at is not None
        assert len(submission.history) == 2
        assert submission.history[1]["action"] == "graded_from_journal"
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_submission_for_nonexistent_lab(
        self,
        mock_db,
        sample_student: User,
        sample_lesson: Lesson,
        sample_teacher: User,
    ):
        async def mock_find_published_lab(db, subject_id, work_number):
            return None

        original_find = journal_sync.find_published_lab
        journal_sync.find_published_lab = mock_find_published_lab
        try:
            submission = await journal_sync.sync_from_journal(
                mock_db,
                sample_student.id,
                sample_lesson,
                work_number=999,
                grade=5,
                comment="Test",
                created_by=sample_teacher.id,
            )
        finally:
            journal_sync.find_published_lab = original_find

        assert submission is None
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_submission_for_lesson_without_subject(
        self,
        mock_db,
        sample_student: User,
        sample_group: Group,
        sample_teacher: User,
    ):
        lesson_without_subject = Lesson(
            group_id=sample_group.id,
            subject_id=None,
            date=datetime.now(timezone.utc).date(),
            lesson_number=1,
            lesson_type=LessonType.LAB,
            work_number=1,
            is_cancelled=False,
        )

        submission = await journal_sync.sync_from_journal(
            mock_db,
            sample_student.id,
            lesson_without_subject,
            work_number=1,
            grade=5,
            comment="Test",
            created_by=sample_teacher.id,
        )

        assert submission is None
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_bulk_grade_creates_multiple_submissions(
        self,
        mock_db,
        sample_group: Group,
        sample_lab: Lab,
        sample_lesson: Lesson,
        sample_teacher: User,
    ):
        students = [
            User(
                full_name=f"Студент {i}",
                username=f"student{i}",
                role=sample_teacher.role.__class__.STUDENT,
                group_id=sample_group.id,
                subgroup=1,
                is_active=True,
            )
            for i in range(1, 4)
        ]
        grades = [5, 4, 3]

        async def mock_find_published_lab(db, subject_id, work_number):
            return sample_lab

        mock_db.execute.side_effect = lambda *args, **kwargs: scalar_result(None)
        original_find = journal_sync.find_published_lab
        journal_sync.find_published_lab = mock_find_published_lab
        try:
            submissions = []
            for student, grade in zip(students, grades):
                submissions.append(
                    await journal_sync.sync_from_journal(
                        mock_db,
                        student.id,
                        sample_lesson,
                        work_number=1,
                        grade=grade,
                        comment=f"Оценка {grade}",
                        created_by=sample_teacher.id,
                    )
                )
        finally:
            journal_sync.find_published_lab = original_find

        assert len(submissions) == 3
        assert all(submission is not None for submission in submissions)
        assert [submission.grade for submission in submissions] == grades
        assert mock_db.add.call_count == 3

    @pytest.mark.asyncio
    async def test_race_condition_handled_correctly(
        self,
        mock_db,
        sample_student: User,
        sample_lab: Lab,
        sample_lesson: Lesson,
        sample_teacher: User,
    ):
        concurrent_submission = make_submission(
            user_id=sample_student.id,
            lab_id=sample_lab.id,
            status=SubmissionStatus.NEW,
        )

        async def mock_find_published_lab(db, subject_id, work_number):
            return sample_lab

        execute_call_count = 0

        def mock_execute_side_effect(*args, **kwargs):
            nonlocal execute_call_count
            execute_call_count += 1
            if execute_call_count == 1:
                return scalar_result(None)
            return scalar_result(concurrent_submission)

        flush_call_count = 0

        async def mock_flush_side_effect():
            nonlocal flush_call_count
            flush_call_count += 1
            if flush_call_count == 1:
                raise IntegrityError("duplicate key", None, None)

        mock_db.execute.side_effect = mock_execute_side_effect
        mock_db.flush.side_effect = mock_flush_side_effect
        original_find = journal_sync.find_published_lab
        journal_sync.find_published_lab = mock_find_published_lab
        try:
            submission = await journal_sync.sync_from_journal(
                mock_db,
                sample_student.id,
                sample_lesson,
                work_number=1,
                grade=5,
                comment="Test",
                created_by=sample_teacher.id,
            )
        finally:
            journal_sync.find_published_lab = original_find

        assert submission is not None
        assert submission.id == concurrent_submission.id
        assert submission.grade == 5
        assert submission.status == SubmissionStatus.ACCEPTED
        assert submission.feedback == "Test"
        assert submission.history[0]["action"] == "graded_from_journal"
        mock_db.rollback.assert_not_called()
