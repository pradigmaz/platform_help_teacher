"""Сервис синхронизации сдач лабораторных работ с журналом."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lab, Lesson, LessonGrade, Submission, SubmissionStatus, User

logger = logging.getLogger(__name__)


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
        result = await db.execute(
            select(Lab).where(
                and_(
                    Lab.subject_id == subject_id, Lab.number == work_number, Lab.is_published, Lab.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()

    async def sync_from_journal(
        self,
        db: AsyncSession,
        student_id: UUID,
        lesson: Lesson,
        work_number: int,
        grade: int,
        comment: str | None,
        created_by: UUID,
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
            submission.grade = grade
            submission.status = SubmissionStatus.ACCEPTED
            submission.feedback = comment
            submission.accepted_at = now

            # Добавляем в историю
            submission.history = submission.history + [
                {
                    "action": "graded_from_journal",
                    "grade": grade,
                    "comment": comment,
                    "by": str(created_by),
                    "at": now.isoformat(),
                }
            ]
        else:
            # Создаём новую сдачу
            logger.info(
                f"[SubmissionJournalSync:sync_from_journal] Creating new submission: student={student_id}, lab={lab.id}"
            )
            submission = Submission(
                user_id=student_id,
                lab_id=lab.id,
                is_manual=True,
                status=SubmissionStatus.ACCEPTED,
                grade=grade,
                feedback=comment,
                accepted_at=now,
                history=[
                    {
                        "action": "created_from_journal",
                        "grade": grade,
                        "comment": comment,
                        "by": str(created_by),
                        "at": now.isoformat(),
                    }
                ],
            )

            try:
                db.add(submission)
                await db.flush()  # Триггер constraint проверки
            except IntegrityError:
                # Race condition: другой запрос уже создал submission
                logger.warning(
                    f"[SubmissionJournalSync:sync_from_journal] Race condition detected, retrying... "
                    f"student={student_id}, lab={lab.id}"
                )
                await db.rollback()

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
                    submission.grade = grade
                    submission.status = SubmissionStatus.ACCEPTED
                    submission.feedback = comment
                    submission.accepted_at = now

                    # Добавляем в историю
                    submission.history = submission.history + [
                        {
                            "action": "graded_from_journal",
                            "grade": grade,
                            "comment": comment,
                            "by": str(created_by),
                            "at": now.isoformat(),
                        }
                    ]
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

    async def find_lesson_for_student(self, db: AsyncSession, lab: Lab, student_id: UUID) -> Lesson | None:
        """
        Найти подходящее занятие для записи оценки.
        Ищет ближайшее прошедшее или сегодняшнее LAB-занятие для группы/подгруппы студента.

        Важно: lesson.work_number может отличаться от lab.number (сдача долга).
        Оценка ставится на текущее занятие, а work_number в lesson_grade = номер сдаваемой лабы.
        """
        from sqlalchemy import or_

        from app.models.schedule import LessonType
        from app.services.schedule_constants import today_msk

        # Загружаем студента с группой
        student = await db.get(User, student_id)
        if not student or not student.group_id:
            return None

        # Если у лабы нет предмета — не можем найти занятие
        if not lab.subject_id:
            return None

        today = today_msk()

        # Ищем ближайшее LAB-занятие на сегодня или раньше
        # НЕ фильтруем по work_number — студент может сдавать долг
        query = (
            select(Lesson)
            .where(
                Lesson.subject_id == lab.subject_id,
                Lesson.group_id == student.group_id,
                Lesson.lesson_type == LessonType.LAB,
                Lesson.date <= today,
                not Lesson.is_cancelled,
                # Подгруппа: либо совпадает, либо занятие для всех (NULL)
                or_(Lesson.subgroup == student.subgroup, Lesson.subgroup.is_(None)),
            )
            .order_by(Lesson.date.desc())  # Ближайшее к сегодня
            .limit(1)
        )

        result = await db.execute(query)
        return result.scalar_one_or_none()

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
