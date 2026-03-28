"""Сервис бизнес-логики для студенческих лабораторных работ."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lab import Lab
from app.models.lesson import Lesson
from app.models.lesson_grade import LessonGrade
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User, UserRole
from app.services.attestation.lab_progress import dedupe_lesson_grade_rows, is_completed_lab_grade
from app.services.lab_lookup import find_active_lab_by_subject_and_number
from app.services.submission_transition import move_submission_to_new, move_submission_to_ready

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
    created_at: datetime | None


def _is_better_grade(
    candidate_grade: int, candidate_created_at: datetime | None, current: _GradeRow | LessonGrade
) -> bool:
    current_created_at = getattr(current, "created_at", None)
    if candidate_grade != current.grade:
        return candidate_grade > current.grade

    if candidate_created_at is None:
        return False
    if current_created_at is None:
        return True
    return candidate_created_at > current_created_at


def resolve_lab_acceptance(
    submission: Submission | None,
    journal_grade: LessonGrade | _GradeRow | None,
) -> tuple[bool, int | None, str | None]:
    """Нормализовать статус сдачи лабы по журналу и submission."""
    journal_grade_value = journal_grade.grade if journal_grade else None
    if journal_grade_value is not None:
        if is_completed_lab_grade(journal_grade_value):
            return True, journal_grade_value, "journal"
        return False, journal_grade_value, None
    if submission and submission.status == SubmissionStatus.ACCEPTED:
        return True, None, "submission"
    return False, None, None


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
            "lg.work_number, lg.grade, lg.comment, lg.created_by, lg.created_at "
            "FROM lesson_grades lg "
            "JOIN lessons l ON CAST(lg.lesson_id AS TEXT) = CAST(l.id AS TEXT) "
            "WHERE CAST(lg.student_id AS TEXT) = :student_id "
            "AND lg.work_number IS NOT NULL "
            "AND l.is_cancelled IS NOT TRUE"
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
            candidate_created_at = row["created_at"]
            if work_number not in journal_grades or _is_better_grade(
                grade, candidate_created_at, journal_grades[work_number]
            ):
                journal_grades[work_number] = _GradeRow(
                    id=row["id"],
                    lesson_id=row["lesson_id"],
                    student_id=row["student_id"],
                    work_number=work_number,
                    grade=grade,
                    comment=row["comment"],
                    created_at=candidate_created_at,
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
            .where(
                LessonGrade.student_id == student_id,
                LessonGrade.work_number.isnot(None),
                LessonModel.is_cancelled.is_(False),
            )
        )
        rows = result.all()
        subject_by_grade_id = {grade.id: subject_id for grade, subject_id in rows}
        grades_by_subject: dict[UUID, dict[int, LessonGrade]] = {}
        for g in dedupe_lesson_grade_rows(rows):
            subject_id = subject_by_grade_id[g.id]
            if subject_id not in grades_by_subject:
                grades_by_subject[subject_id] = {}
            subj_grades = grades_by_subject[subject_id]
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
        prev_lab = await find_active_lab_by_subject_and_number(db, lab.subject_id, lab.number - 1, published_only=True)
        if not prev_lab:
            return True
        prev_sub = await db.execute(
            select(Submission).where(
                Submission.user_id == user_id,
                Submission.lab_id == prev_lab.id,
                Submission.status == SubmissionStatus.ACCEPTED,
            )
        )
        previous_submission = prev_sub.scalar_one_or_none()
        journal_grades_by_subject = await self.get_user_journal_grades_by_subject(db, user_id)
        previous_journal_grade = journal_grades_by_subject.get(prev_lab.subject_id, {}).get(prev_lab.number)
        return resolve_lab_acceptance(previous_submission, previous_journal_grade)[0]

    async def mark_ready(
        self,
        db: AsyncSession,
        user_id: UUID,
        lab_id: UUID,
        variant_number: int | None,
        lesson: Lesson | None = None,
    ) -> Submission:
        """Поставить submission в очередь на сдачу."""
        now = datetime.now(UTC)
        sub = await self.get_user_submission_for_lab(db, user_id, lab_id)
        if sub:
            if sub.status == SubmissionStatus.READY:
                raise ValueError("Already in queue")
            if sub.status == SubmissionStatus.ACCEPTED:
                lab = await self.get_lab_by_id(db, lab_id)
                journal_grade = None
                if lab and lab.subject_id:
                    journal_grades_by_subject = await self.get_user_journal_grades_by_subject(db, user_id)
                    journal_grade = journal_grades_by_subject.get(lab.subject_id, {}).get(lab.number)

                if resolve_lab_acceptance(sub, journal_grade)[0]:
                    raise ValueError("Lab already accepted")
            move_submission_to_ready(sub, ready_at=now, variant_number=variant_number, lesson=lesson)
        else:
            sub = Submission(
                user_id=user_id,
                lab_id=lab_id,
                status=SubmissionStatus.NEW,
                is_manual=True,
            )
            db.add(sub)
            move_submission_to_ready(sub, ready_at=now, variant_number=variant_number, lesson=lesson)
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
        move_submission_to_new(sub)
        await db.commit()
        logger.info(f"Student {user_id} cancelled ready for lab {lab_id}")


student_lab_service = StudentLabService()
