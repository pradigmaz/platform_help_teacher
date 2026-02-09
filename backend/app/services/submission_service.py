"""Сервис бизнес-логики для сдачи лабораторных работ."""
import logging
from typing import Optional, Any
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Submission, SubmissionStatus, Lab, LessonGrade, User
from app.services.attestation.deadline_validator import get_max_allowed_grade_for_lab
from app.services.attestation.lab_slot_validator import get_grades_count_on_lesson, get_max_labs_per_lesson
from app.services.submission_journal_sync import journal_sync

logger = logging.getLogger(__name__)


class SubmissionService:
    """Сервис для управления сдачами лабораторных работ."""

    async def get_by_id(
        self,
        db: AsyncSession,
        submission_id: UUID,
        load_relations: bool = False
    ) -> Optional[Submission]:
        """Получить сдачу по ID."""
        query = select(Submission).where(Submission.id == submission_id)
        if load_relations:
            query = query.options(
                selectinload(Submission.user).selectinload(User.group),
                selectinload(Submission.lab)
            )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def accept(
        self,
        db: AsyncSession,
        submission: Submission,
        grade: int,
        comment: Optional[str],
        accepted_by: UUID
    ) -> dict[str, Any]:
        """
        Принять работу студента.
        Автоматически синхронизирует с журналом если есть привязка к занятию.
        Проверяет дедлайны и слоты.
        """
        if submission.status != SubmissionStatus.READY:
            raise ValueError(f"Cannot accept submission with status {submission.status.value}")
        
        # Валидация дедлайна и слотов
        await self._validate_grade_constraints(db, submission, grade)

        now = datetime.now(timezone.utc)
        
        # Обновляем Submission
        submission.status = SubmissionStatus.ACCEPTED
        submission.grade = grade
        submission.feedback = comment
        submission.accepted_at = now
        
        # Добавляем в историю
        submission.history = submission.history + [{
            "action": "accepted",
            "grade": grade,
            "comment": comment,
            "by": str(accepted_by),
            "at": now.isoformat(),
        }]
        
        # Синхронизация с журналом
        lesson_grade_synced = await journal_sync.sync_with_journal(
            db, submission, grade, comment, accepted_by
        )
        
        await db.commit()
        logger.info(f"Submission {submission.id} accepted with grade {grade}")
        
        return {
            "status": "accepted",
            "submission_id": str(submission.id),
            "grade": grade,
            "lesson_grade_synced": lesson_grade_synced,
        }

    async def reject(
        self,
        db: AsyncSession,
        submission: Submission,
        comment: str,
        rejected_by: UUID
    ) -> dict[str, Any]:
        """Отклонить работу студента."""
        if submission.status != SubmissionStatus.READY:
            raise ValueError(f"Cannot reject submission with status {submission.status.value}")

        now = datetime.now(timezone.utc)
        
        submission.status = SubmissionStatus.REJECTED
        submission.feedback = comment
        
        # Добавляем в историю
        submission.history = submission.history + [{
            "action": "rejected",
            "comment": comment,
            "by": str(rejected_by),
            "at": now.isoformat(),
        }]
        
        await db.commit()
        logger.info(f"Submission {submission.id} rejected")
        
        return {
            "status": "rejected",
            "submission_id": str(submission.id),
            "comment": comment,
        }

    async def _validate_grade_constraints(
        self,
        db: AsyncSession,
        submission: Submission,
        grade: int
    ) -> None:
        """Проверить дедлайн и слоты перед принятием работы."""
        # Загружаем lab если не загружен
        if not submission.lab:
            result = await db.execute(select(Lab).where(Lab.id == submission.lab_id))
            lab = result.scalar_one_or_none()
        else:
            lab = submission.lab
        
        if not lab or not lab.subject_id:
            return  # Нет привязки к предмету — нет ограничений
        
        # Ищем занятие для студента
        lesson = await journal_sync.find_lesson_for_student(db, lab, submission.user_id)
        if not lesson:
            return  # Нет занятия — нет ограничений
        
        # Проверяем дедлайн
        max_allowed = await get_max_allowed_grade_for_lab(
            db, lab, lesson, submission.user_id
        )
        if grade > max_allowed:
            raise ValueError(
                f"Максимальная оценка для этой работы: {max_allowed} (просрочка дедлайна)"
            )
        
        # Проверяем слоты (только для новых оценок)
        existing = await db.execute(
            select(LessonGrade).where(and_(
                LessonGrade.lesson_id == lesson.id,
                LessonGrade.student_id == submission.user_id,
                LessonGrade.work_number == lab.number,
            ))
        )
        if existing.scalar_one_or_none() is None:
            # Новая оценка — проверяем слоты
            current_count = await get_grades_count_on_lesson(
                db, submission.user_id, lesson.id
            )
            max_labs = await get_max_labs_per_lesson(
                db, submission.user_id, lesson.subject_id
            )
            if current_count >= max_labs:
                raise ValueError(
                    f"Лимит лаб за занятие: {max_labs} (уже сдано: {current_count})"
                )


submission_service = SubmissionService()
