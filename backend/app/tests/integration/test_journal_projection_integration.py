from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models import Group, Lab, Lesson, LessonType, Submission, SubmissionStatus, Subject, User, UserRole
from app.services.journal_grade_service import JournalGradeWriteService

pytestmark = pytest.mark.integration


def build_entities(suffix: str):
    group = Group(
        code=f"IT{suffix[:6]}",
        name=f"Integration {suffix[:6]}",
        invite_code=suffix[:8],
    )
    student = User(
        full_name=f"Student {suffix}",
        username=f"student_{suffix}",
        role=UserRole.STUDENT,
        group=group,
        subgroup=1,
        is_active=True,
    )
    teacher = User(
        full_name=f"Teacher {suffix}",
        username=f"teacher_{suffix}",
        role=UserRole.TEACHER,
        is_active=True,
    )
    subject = Subject(name=f"Subject {suffix}", code=f"S{suffix[:6]}")
    lesson = Lesson(
        group=group,
        subject=subject,
        date=date(2026, 4, 2),
        lesson_number=1,
        lesson_type=LessonType.LAB,
        work_number=1,
        subgroup=1,
    )
    lab = Lab(
        subject=subject,
        lesson=lesson,
        number=1,
        title=f"Lab {suffix}",
        is_published=True,
        max_grade=5,
    )
    return group, student, teacher, subject, lesson, lab


@pytest.mark.asyncio
async def test_write_grade_creates_and_updates_submission_projection():
    suffix = uuid4().hex[:8]
    service = JournalGradeWriteService()

    async with AsyncSessionLocal() as session, session.begin():
        group, student, teacher, subject, lesson, lab = build_entities(suffix)
        session.add_all([group, student, teacher, subject, lesson, lab])
        await session.flush()

        grade = await service.upsert_grade(
            session,
            lesson=lesson,
            student_id=student.id,
            grade=5,
            work_number=1,
            comment="Initial sync",
            actor_id=teacher.id,
        )

        submission = (
            await session.execute(select(Submission).where(Submission.user_id == student.id, Submission.lab_id == lab.id))
        ).scalar_one()
        assert grade.grade == 5
        assert submission.status == SubmissionStatus.ACCEPTED
        assert submission.grade == 5
        assert submission.feedback == "Initial sync"
        assert submission.lesson_id == lesson.id
        assert len(submission.history) == 1

        updated_grade = await service.upsert_grade(
            session,
            lesson=lesson,
            student_id=student.id,
            grade=4,
            work_number=1,
            comment="Updated sync",
            actor_id=teacher.id,
        )

        refreshed_submission = (
            await session.execute(select(Submission).where(Submission.user_id == student.id, Submission.lab_id == lab.id))
        ).scalar_one()
        assert updated_grade.id == grade.id
        assert refreshed_submission.id == submission.id
        assert refreshed_submission.grade == 4
        assert refreshed_submission.feedback == "Updated sync"
        assert len(refreshed_submission.history) == 2

        await session.rollback()


@pytest.mark.asyncio
async def test_delete_grade_rolls_submission_back_to_new_state():
    suffix = uuid4().hex[:8]
    service = JournalGradeWriteService()

    async with AsyncSessionLocal() as session, session.begin():
        group, student, teacher, subject, lesson, lab = build_entities(suffix)
        session.add_all([group, student, teacher, subject, lesson, lab])
        await session.flush()

        grade = await service.upsert_grade(
            session,
            lesson=lesson,
            student_id=student.id,
            grade=5,
            work_number=1,
            comment="Initial sync",
            actor_id=teacher.id,
        )

        await service.delete_grade(session, grade, actor_id=teacher.id)

        submission = (
            await session.execute(select(Submission).where(Submission.user_id == student.id, Submission.lab_id == lab.id))
        ).scalar_one()
        deleted_grade = await session.get(type(grade), grade.id)

        assert deleted_grade is None
        assert submission.status == SubmissionStatus.NEW
        assert submission.grade is None
        assert submission.feedback is None
        assert submission.lesson_id is None
        assert submission.lesson_date is None
        assert submission.lesson_number is None
        assert submission.history[-1]["action"] == "grade_removed_from_journal"

        await session.rollback()
