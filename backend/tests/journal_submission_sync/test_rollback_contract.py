"""Contract tests for rollback of the journal -> submission projection."""

from datetime import datetime, timezone

import pytest

from app.models import Lab, Lesson, Subject, SubmissionStatus, User
from app.services.submission_journal_sync import journal_sync

from .conftest import make_submission, scalar_result


class TestRollbackFromJournalContract:
    @pytest.mark.asyncio
    async def test_rollback_updates_submission_for_unpublished_lab(
        self,
        mock_db,
        sample_student: User,
        sample_lab: Lab,
        sample_lesson: Lesson,
        sample_teacher: User,
    ):
        sample_lab.is_published = False
        sample_lab.deleted_at = datetime.now(timezone.utc)
        submission = make_submission(
            user_id=sample_student.id,
            lab_id=sample_lab.id,
            status=SubmissionStatus.ACCEPTED,
            is_manual=True,
            grade=5,
            feedback="OK",
        )
        mock_db.execute.return_value = scalar_result(submission)

        rolled_back = await journal_sync.rollback_from_journal(
            mock_db,
            student_id=sample_student.id,
            lesson=sample_lesson,
            work_number=sample_lab.number,
            created_by=sample_teacher.id,
        )

        assert rolled_back is True
        assert submission.status == SubmissionStatus.NEW
        assert submission.grade is None
        assert submission.feedback is None
        assert submission.accepted_at is None
        assert submission.lesson_id is None
        assert submission.lesson_date is None
        assert submission.lesson_number is None
        assert submission.history[-1]["action"] == "grade_removed_from_journal"

    @pytest.mark.asyncio
    async def test_find_published_lab_ignores_deleted(
        self,
        mock_db,
        sample_subject: Subject,
    ):
        deleted_lab = Lab(
            number=1,
            subject_id=sample_subject.id,
            title="Удалённая лаба",
            is_published=True,
            deleted_at=datetime.now(timezone.utc),
        )
        mock_db.execute.return_value = scalar_result(None)

        lab = await journal_sync.find_published_lab(
            mock_db,
            sample_subject.id,
            work_number=deleted_lab.number,
        )

        assert lab is None

    @pytest.mark.asyncio
    async def test_find_published_lab_ignores_unpublished(
        self,
        mock_db,
        sample_subject: Subject,
    ):
        unpublished_lab = Lab(
            number=1,
            subject_id=sample_subject.id,
            title="Неопубликованная лаба",
            is_published=False,
            deleted_at=None,
        )
        mock_db.execute.return_value = scalar_result(None)

        lab = await journal_sync.find_published_lab(
            mock_db,
            sample_subject.id,
            work_number=unpublished_lab.number,
        )

        assert lab is None
