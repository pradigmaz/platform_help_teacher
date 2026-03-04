"""Сервис бизнес-логики для студенческих лабораторных работ."""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lab import Lab
from app.models.lesson_grade import LessonGrade
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


class StudentLabService:
    """Сервис для работы студентов с лабораторными."""

    async def get_published_labs(self, db: AsyncSession) -> list[Lab]:
        """Получить все опубликованные лабы."""
        result = await db.execute(
            select(Lab)
            .where(Lab.is_published.is_(True))
            .where(Lab.deleted_at.is_(None))
            .order_by(Lab.number.asc(), Lab.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_lab_by_id(self, db: AsyncSession, lab_id: UUID) -> Lab | None:
        """Получить лабу по ID."""
        return await db.get(Lab, lab_id)

    async def get_user_submissions(self, db: AsyncSession, user_id: UUID) -> dict[UUID, Submission]:
        """Получить все submissions пользователя как dict {lab_id: submission}."""
        result = await db.execute(select(Submission).where(Submission.user_id == user_id))
        return {s.lab_id: s for s in result.scalars().all()}

    async def get_user_submission_for_lab(self, db: AsyncSession, user_id: UUID, lab_id: UUID) -> Submission | None:
        """Получить последнюю submission пользователя для конкретной лабы."""
        result = await db.execute(
            select(Submission)
            .where(
                Submission.user_id == user_id,
                Submission.lab_id == lab_id,
            )
            .order_by(Submission.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_user_journal_grades(self, db: AsyncSession, student_id: UUID) -> dict[int, LessonGrade]:
        """Получить лучшие оценки из журнала по work_number."""
        result = await db.execute(
            select(LessonGrade).where(
                LessonGrade.student_id == student_id,
                LessonGrade.work_number.isnot(None)
            )
        )
        journal_grades: dict[int, LessonGrade] = {}
        for g in result.scalars().all():
            if g.work_number not in journal_grades or g.grade > journal_grades[g.work_number].grade:
                journal_grades[g.work_number] = g
        return journal_grades

    async def get_student_position(self, db: AsyncSession, user: User) -> int | None:
        """Получить позицию студента в списке группы."""
        if not user.group_id:
            return None
        result = await db.execute(
            select(User)
            .where(User.group_id == user.group_id, User.role == UserRole.STUDENT)
            .order_by(User.full_name.asc())
        )
        students = result.scalars().all()
        for i, student in enumerate(students):
            if student.id == user.id:
                return i + 1
        return None

    async def check_lab_availability(self, db: AsyncSession, user_id: UUID, lab: Lab) -> bool:
        """Проверить доступность лабы (предыдущая сдана)."""
        if lab.number == 1 or not lab.is_sequential:
            return True
        prev_result = await db.execute(
            select(Lab).where(
                Lab.subject_id == lab.subject_id,
                Lab.number == lab.number - 1,
            )
        )
        prev_lab = prev_result.scalar_one_or_none()
        if not prev_lab:
            return True
        prev_sub = await db.execute(
            select(Submission).where(
                Submission.user_id == user_id,
                Submission.lab_id == prev_lab.id,
                Submission.status == SubmissionStatus.ACCEPTED,
            )
        )
        return prev_sub.scalar_one_or_none() is not None

    async def mark_ready(
        self,
        db: AsyncSession,
        user_id: UUID,
        lab_id: UUID,
        variant_number: int | None,
    ) -> Submission:
        """Поставить submission в очередь на сдачу."""
        sub = await self.get_user_submission_for_lab(db, user_id, lab_id)
        if sub:
            if sub.status == SubmissionStatus.READY:
                raise ValueError("Already in queue")
            if sub.status == SubmissionStatus.ACCEPTED:
                raise ValueError("Lab already accepted")
            sub.status = SubmissionStatus.READY
            sub.ready_at = datetime.utcnow()
            sub.variant_number = variant_number
        else:
            sub = Submission(
                user_id=user_id,
                lab_id=lab_id,
                status=SubmissionStatus.READY,
                is_manual=True,
                variant_number=variant_number,
                ready_at=datetime.utcnow(),
            )
            db.add(sub)
        await db.commit()
        await db.refresh(sub)
        logger.info(f"Student {user_id} marked lab {lab_id} as ready, variant={variant_number}")
        return sub

    async def cancel_ready(self, db: AsyncSession, user_id: UUID, lab_id: UUID) -> None:
        """Отменить готовность к сдаче."""
        sub = await self.get_user_submission_for_lab(db, user_id, lab_id)
        if not sub:
            raise ValueError("Submission not found")
        if sub.status != SubmissionStatus.READY:
            raise ValueError("Not in queue")
        sub.status = SubmissionStatus.NEW
        sub.ready_at = None
        await db.commit()
        logger.info(f"Student {user_id} cancelled ready for lab {lab_id}")


student_lab_service = StudentLabService()
