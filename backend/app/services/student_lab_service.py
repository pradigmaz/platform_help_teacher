"""Сервис бизнес-логики для студенческих лабораторных работ."""

import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lab import Lab
from app.models.lesson_grade import LessonGrade
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


@dataclass
class _GradeRow:
    """Lightweight результат get_user_journal_grades — совместим с PostgreSQL и SQLite."""

    id: str
    lesson_id: str
    student_id: str
    work_number: int
    grade: int
    comment: str | None


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
        """Получить лабу по ID (только опубликованные и не удалённые)."""
        result = await db.execute(
            select(Lab).where(Lab.id == lab_id, Lab.is_published.is_(True), Lab.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

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

    async def get_user_journal_grades(
        self, db: AsyncSession, student_id: UUID, subject_id: UUID | None = None
    ) -> "dict[int, _GradeRow]":
        """Получить лучшие оценки из журнала по work_number.

        Args:
            subject_id: если указан — фильтрует по предмету (исправляет BUG-7).
                        Если None — возвращает все оценки (обратная совместимость).

        Returns:
            dict {work_number: _GradeRow} с атрибутами .grade, .lesson_id
        """
        from sqlalchemy import text

        # Raw SQL с явным CAST для совместимости PostgreSQL (UUID) и SQLite (Text)
        sql = (
            "SELECT lg.id, CAST(lg.lesson_id AS TEXT) AS lesson_id, "
            "CAST(lg.student_id AS TEXT) AS student_id, "
            "lg.work_number, lg.grade, lg.comment, lg.created_by "
            "FROM lesson_grades lg "
            "JOIN lessons l ON CAST(lg.lesson_id AS TEXT) = CAST(l.id AS TEXT) "
            "WHERE CAST(lg.student_id AS TEXT) = :student_id "
            "AND lg.work_number IS NOT NULL"
        )
        params: dict = {"student_id": str(student_id)}

        if subject_id is not None:
            sql += " AND CAST(l.subject_id AS TEXT) = :subject_id"
            params["subject_id"] = str(subject_id)

        result = await db.execute(text(sql), params)
        rows = result.mappings().all()

        journal_grades: dict[int, _GradeRow] = {}
        for row in rows:
            work_number = row["work_number"]
            grade = row["grade"]
            if work_number is None:
                continue
            if work_number not in journal_grades or grade > journal_grades[work_number].grade:
                journal_grades[work_number] = _GradeRow(
                    id=row["id"],
                    lesson_id=row["lesson_id"],
                    student_id=row["student_id"],
                    work_number=work_number,
                    grade=grade,
                    comment=row["comment"],
                )
        return journal_grades

    async def get_user_journal_grades_by_subject(
        self, db: AsyncSession, student_id: UUID
    ) -> dict[UUID, dict[int, LessonGrade]]:
        """Получить лучшие оценки из журнала, сгруппированные по subject_id.

        Возвращает: {subject_id: {work_number: LessonGrade}}
        """
        from app.models.lesson import Lesson as LessonModel

        result = await db.execute(
            select(LessonGrade, LessonModel.subject_id)
            .join(LessonModel, LessonGrade.lesson_id == LessonModel.id)
            .where(LessonGrade.student_id == student_id, LessonGrade.work_number.isnot(None))
        )
        grades_by_subject: dict[UUID, dict[int, LessonGrade]] = {}
        for g, subject_id in result.all():
            if subject_id not in grades_by_subject:
                grades_by_subject[subject_id] = {}
            subj_grades = grades_by_subject[subject_id]
            if g.work_number not in subj_grades or g.grade > subj_grades[g.work_number].grade:
                subj_grades[g.work_number] = g
        return grades_by_subject

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
