"""Projection sync between journal grades and submissions."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lab, Lesson, LessonGrade, Submission, SubmissionStatus, User
from app.services.acceptance_lesson_resolver import find_latest_lesson_for_student
from app.services.lab_lookup import find_active_lab_by_subject_and_number
from app.services.submission_transition import (
    clear_submission_lesson_context,
    move_submission_to_accepted,
    move_submission_to_new,
)

logger = logging.getLogger(__name__)


def _append_history(submission: Submission, event: dict) -> None:
    """Append history event without assuming legacy rows always have a JSON list."""
    submission.history = (submission.history or []) + [event]


class SubmissionJournalSync:
    """Сервис синхронизации Submission ↔ Journal (LessonGrade)."""

    async def find_published_lab(self, db: AsyncSession, subject_id: UUID, work_number: int) -> Lab | None:
        """
        Найти опубликованную лабу по subject_id и номеру работы.

        Args:
            db: Сессия БД
            subject_id: ID предмета
            work_number: Номер работы

        Returns:
            Lab или None если не найдена
        """
        return await find_active_lab_by_subject_and_number(db, subject_id, work_number, published_only=True)

    async def sync_from_journal(
        self,
        db: AsyncSession,
        student_id: UUID,
        lesson: Lesson,
        work_number: int,
        grade: int,
        comment: str | None,
        created_by: UUID,
        append_history: bool = True,
    ) -> Submission | None:
        """
        Создать или обновить Submission на основе оценки из журнала.

        Args:
            db: Сессия БД
            student_id: ID студента
            lesson: Занятие из журнала
            work_number: Номер работы
            grade: Оценка
            comment: Комментарий
            created_by: ID преподавателя

        Returns:
            Submission или None если лаба не найдена
        """
        logger.info(
            f"[SubmissionJournalSync:sync_from_journal] Starting sync: "
            f"student={student_id}, lesson={lesson.id}, work_number={work_number}, grade={grade}"
        )

        # Проверяем что у занятия есть subject_id
        if not lesson.subject_id:
            logger.warning(f"[SubmissionJournalSync:sync_from_journal] Lesson {lesson.id} has no subject_id")
            return None

        # Ищем опубликованную лабу
        lab = await self.find_published_lab(db, lesson.subject_id, work_number)
        if not lab:
            logger.info(
                f"[SubmissionJournalSync:sync_from_journal] No published lab found: "
                f"subject={lesson.subject_id}, number={work_number}"
            )
            return None

        # Ищем существующую сдачу
        result = await db.execute(
            select(Submission).where(
                and_(Submission.user_id == student_id, Submission.lab_id == lab.id, Submission.deleted_at.is_(None))
            )
        )
        submission = result.scalar_one_or_none()

        now = datetime.now(UTC)

        if submission:
            # Обновляем существующую сдачу
            logger.info(f"[SubmissionJournalSync:sync_from_journal] Updating existing submission {submission.id}")
            move_submission_to_accepted(
                submission,
                grade=grade,
                comment=comment,
                accepted_at=now,
                lesson_id=lesson.id,
                lesson_date=lesson.date,
                lesson_number=lesson.lesson_number,
            )

            # Добавляем в историю
            if append_history:
                _append_history(
                    submission,
                    {
                        "action": "graded_from_journal",
                        "grade": grade,
                        "comment": comment,
                        "by": str(created_by),
                        "at": now.isoformat(),
                    },
                )
        else:
            # Создаём новую сдачу
            logger.info(
                f"[SubmissionJournalSync:sync_from_journal] Creating new submission: student={student_id}, lab={lab.id}"
            )
            submission = Submission(
                user_id=student_id,
                lab_id=lab.id,
                is_manual=True,
                history=(
                    [
                        {
                            "action": "created_from_journal",
                            "grade": grade,
                            "comment": comment,
                            "by": str(created_by),
                            "at": now.isoformat(),
                        }
                    ]
                    if append_history
                    else []
                ),
            )
            move_submission_to_accepted(
                submission,
                grade=grade,
                comment=comment,
                accepted_at=now,
                lesson_id=lesson.id,
                lesson_date=lesson.date,
                lesson_number=lesson.lesson_number,
            )

            try:
                async with db.begin_nested():
                    db.add(submission)
                    await db.flush()  # Триггер constraint проверки
            except IntegrityError:
                # Race condition: другой запрос уже создал submission
                logger.warning(
                    f"[SubmissionJournalSync:sync_from_journal] Race condition detected, retrying... "
                    f"student={student_id}, lab={lab.id}"
                )

                # Повторяем SELECT — submission уже создан
                result = await db.execute(
                    select(Submission).where(
                        and_(
                            Submission.user_id == student_id,
                            Submission.lab_id == lab.id,
                            Submission.deleted_at.is_(None),
                        )
                    )
                )
                submission = result.scalar_one_or_none()

                if submission:
                    # Обновляем найденный submission
                    logger.info(
                        f"[SubmissionJournalSync:sync_from_journal] Found existing submission after race, updating {submission.id}"
                    )
                    move_submission_to_accepted(
                        submission,
                        grade=grade,
                        comment=comment,
                        accepted_at=now,
                        lesson_id=lesson.id,
                        lesson_date=lesson.date,
                        lesson_number=lesson.lesson_number,
                    )

                    # Добавляем в историю
                    if append_history:
                        _append_history(
                            submission,
                            {
                                "action": "graded_from_journal",
                                "grade": grade,
                                "comment": comment,
                                "by": str(created_by),
                                "at": now.isoformat(),
                            },
                        )
                else:
                    # Не должно произойти, но на всякий случай
                    logger.error(
                        f"[SubmissionJournalSync:sync_from_journal] Submission not found after IntegrityError: "
                        f"student={student_id}, lab={lab.id}"
                    )
                    return None

        logger.info(
            f"[SubmissionJournalSync:sync_from_journal] Successfully synced submission for "
            f"student={student_id}, lab={lab.id}, grade={grade}"
        )
        return submission

    async def rollback_from_journal(
        self,
        db: AsyncSession,
        student_id: UUID,
        lesson: Lesson,
        work_number: int,
        created_by: UUID | None = None,
        append_history: bool = True,
    ) -> bool:
        """Rollback submission projection after grade removal or work-number move."""
        if not lesson.subject_id:
            return False

        result = await db.execute(
            select(Submission)
            .join(Lab, Submission.lab_id == Lab.id)
            .where(
                and_(
                    Submission.user_id == student_id,
                    Submission.deleted_at.is_(None),
                    Lab.subject_id == lesson.subject_id,
                    Lab.number == work_number,
                )
            )
        )
        submission = result.scalar_one_or_none()
        if not submission:
            return False

        now = datetime.now(UTC)
        move_submission_to_new(submission)
        clear_submission_lesson_context(submission)
        submission.feedback = None
        if append_history:
            _append_history(
                submission,
                {
                    "action": "grade_removed_from_journal",
                    "work_number": work_number,
                    "by": str(created_by) if created_by else None,
                    "at": now.isoformat(),
                },
            )
        return True

    async def find_lesson_for_student(self, db: AsyncSession, lab: Lab, student_id: UUID) -> Lesson | None:
        """
        Найти подходящее занятие для записи оценки.
        Ищет ближайшее прошедшее или сегодняшнее LAB-занятие для группы/подгруппы студента.

        Важно: lesson.work_number может отличаться от lab.number (сдача долга).
        Оценка ставится на текущее занятие, а work_number в lesson_grade = номер сдаваемой лабы.
        """
        # Загружаем студента с группой
        student = await db.get(User, student_id)
        if not student or not student.group_id:
            return None

        # Если у лабы нет предмета — не можем найти занятие
        subject_id = getattr(lab, "subject_id", None)
        if not isinstance(subject_id, UUID):
            return None

        return await find_latest_lesson_for_student(db, student=student, subject_id=subject_id)

    async def sync_with_journal(
        self, db: AsyncSession, submission: Submission, grade: int, comment: str | None, created_by: UUID
    ) -> bool:
        """Синхронизировать оценку с журналом (LessonGrade)."""
        # Нужно загрузить lab если не загружен
        if not submission.lab:
            result = await db.execute(select(Lab).where(Lab.id == submission.lab_id))
            lab = result.scalar_one_or_none()
        else:
            lab = submission.lab

        if not lab:
            return False

        # Ищем подходящее занятие для студента
        lesson = await self.find_lesson_for_student(db, lab, submission.user_id)
        if not lesson:
            logger.warning(f"No lesson found for student {submission.user_id}, lab {lab.id}, subject {lab.subject_id}")
            return False

        # Проверяем существующую оценку
        existing = await db.execute(
            select(LessonGrade).where(
                and_(
                    LessonGrade.lesson_id == lesson.id,
                    LessonGrade.student_id == submission.user_id,
                    LessonGrade.work_number == lab.number,
                )
            )
        )
        lesson_grade = existing.scalar_one_or_none()

        if lesson_grade:
            lesson_grade.grade = grade
            lesson_grade.comment = comment
        else:
            lesson_grade = LessonGrade(
                lesson_id=lesson.id,
                student_id=submission.user_id,
                work_number=lab.number,
                grade=grade,
                comment=comment,
                created_by=created_by,
            )
            db.add(lesson_grade)

        logger.info(f"Synced grade {grade} for student {submission.user_id} to lesson {lesson.id} (work #{lab.number})")
        return True


journal_sync = SubmissionJournalSync()
