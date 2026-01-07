"""Сервис бизнес-логики для сдачи лабораторных работ."""
import logging
from typing import Optional, Any
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Submission, SubmissionStatus, Lab, LessonGrade, User

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
        """
        if submission.status != SubmissionStatus.READY:
            raise ValueError(f"Cannot accept submission with status {submission.status.value}")

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
        lesson_grade_synced = await self._sync_with_journal(
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

    async def _sync_with_journal(
        self,
        db: AsyncSession,
        submission: Submission,
        grade: int,
        comment: Optional[str],
        created_by: UUID
    ) -> bool:
        """Синхронизировать оценку с журналом (LessonGrade)."""
        # Нужно загрузить lab если не загружен
        if not submission.lab:
            result = await db.execute(
                select(Lab).where(Lab.id == submission.lab_id)
            )
            lab = result.scalar_one_or_none()
        else:
            lab = submission.lab
        
        if not lab or not lab.lesson_id:
            return False
        
        # Проверяем существующую оценку
        existing = await db.execute(
            select(LessonGrade).where(and_(
                LessonGrade.lesson_id == lab.lesson_id,
                LessonGrade.student_id == submission.user_id,
                LessonGrade.work_number == lab.number,
            ))
        )
        lesson_grade = existing.scalar_one_or_none()
        
        if lesson_grade:
            lesson_grade.grade = grade
            lesson_grade.comment = comment
        else:
            lesson_grade = LessonGrade(
                lesson_id=lab.lesson_id,
                student_id=submission.user_id,
                work_number=lab.number,
                grade=grade,
                comment=comment,
                created_by=created_by,
            )
            db.add(lesson_grade)
        
        return True


submission_service = SubmissionService()
