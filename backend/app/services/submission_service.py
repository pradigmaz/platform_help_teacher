"""Сервис бизнес-логики для сдачи лабораторных работ."""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Lab, Lesson, Submission, SubmissionStatus, User
from app.services.journal_grade_service import (
    JournalGradeConflictError,
    JournalGradeValidationError,
    journal_grade_service,
)
from app.services.submission_journal_sync import journal_sync

logger = logging.getLogger(__name__)


class SubmissionService:
    """Сервис для управления сдачами лабораторных работ."""

    async def get_by_id(self, db: AsyncSession, submission_id: UUID, load_relations: bool = False) -> Submission | None:
        """Получить сдачу по ID."""
        query = select(Submission).where(Submission.id == submission_id)
        if load_relations:
            query = query.options(selectinload(Submission.user).selectinload(User.group), selectinload(Submission.lab))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def accept(
        self, db: AsyncSession, submission: Submission, grade: int, comment: str | None, accepted_by: UUID
    ) -> dict[str, Any]:
        """
        Принять работу студента.
        Пишет каноническую оценку в LessonGrade и отражает результат в Submission.
        """
        if submission.status != SubmissionStatus.READY:
            raise ValueError(f"Cannot accept submission with status {submission.status.value}")

        lab, lesson = await self._resolve_acceptance_context(db, submission)

        now = datetime.now(UTC)

        # Обновляем Submission
        if lesson is not None:
            submission.lesson_id = lesson.id
            submission.lesson_date = lesson.date
            submission.lesson_number = lesson.lesson_number
        submission.status = SubmissionStatus.ACCEPTED
        submission.grade = grade
        submission.feedback = comment
        submission.accepted_at = now

        # Добавляем в историю
        submission.history = submission.history + [
            {
                "action": "accepted",
                "grade": grade,
                "comment": comment,
                "by": str(accepted_by),
                "at": now.isoformat(),
            }
        ]

        lesson_grade_synced = False
        if lesson and lab:
            try:
                await journal_grade_service.write_grade(
                    db=db,
                    lesson=lesson,
                    student_id=submission.user_id,
                    grade=grade,
                    work_number=lab.number,
                    comment=comment,
                    actor_id=accepted_by,
                    sync_submission=True,
                    submission_history=False,
                )
            except (JournalGradeValidationError, JournalGradeConflictError) as exc:
                raise ValueError(str(exc)) from exc
            lesson_grade_synced = True

        await db.commit()
        logger.info(f"Submission {submission.id} accepted with grade {grade}")

        return {
            "status": "accepted",
            "submission_id": str(submission.id),
            "grade": grade,
            "lesson_grade_synced": lesson_grade_synced,
        }

    async def reject(self, db: AsyncSession, submission: Submission, comment: str, rejected_by: UUID) -> dict[str, Any]:
        """Отклонить работу студента."""
        if submission.status != SubmissionStatus.READY:
            raise ValueError(f"Cannot reject submission with status {submission.status.value}")

        now = datetime.now(UTC)

        submission.status = SubmissionStatus.REJECTED
        submission.feedback = comment

        # Добавляем в историю
        submission.history = submission.history + [
            {
                "action": "rejected",
                "comment": comment,
                "by": str(rejected_by),
                "at": now.isoformat(),
            }
        ]

        await db.commit()
        logger.info(f"Submission {submission.id} rejected")

        return {
            "status": "rejected",
            "submission_id": str(submission.id),
            "comment": comment,
        }

    async def resolve_acceptance_context(self, db: AsyncSession, submission: Submission):
        """Public wrapper for lesson/lab resolution shared by queue preview and accept."""
        return await self._resolve_acceptance_context(db, submission)

    async def _resolve_acceptance_context(self, db: AsyncSession, submission: Submission):
        """Resolve lab and target lesson for canonical grade write."""
        if not submission.lab:
            result = await db.execute(select(Lab).where(Lab.id == submission.lab_id))
            lab = result.scalar_one_or_none()
        else:
            lab = submission.lab

        subject_id = getattr(lab, "subject_id", None) if lab else None
        if not lab or not isinstance(subject_id, UUID):
            return lab, None

        lesson = None
        if submission.lesson_id:
            lesson = await db.get(Lesson, submission.lesson_id)

        if lesson is None and submission.lesson_date and submission.lesson_number is not None:
            conditions = [
                Lesson.subject_id == subject_id,
                Lesson.date == submission.lesson_date,
                Lesson.lesson_number == submission.lesson_number,
            ]
            if submission.user and submission.user.group_id:
                conditions.append(Lesson.group_id == submission.user.group_id)
            lesson_result = await db.execute(select(Lesson).where(and_(*conditions)))
            lesson = lesson_result.scalar_one_or_none()

        if lesson is None:
            lesson = await journal_sync.find_lesson_for_student(db, lab, submission.user_id)
        if not lesson:
            raise ValueError("Не найдено занятие для синхронизации приёмки с журналом")

        return lab, lesson


submission_service = SubmissionService()
