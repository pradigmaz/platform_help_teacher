"""Unified write-path for journal grades and submission projection."""

import logging
from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_lesson_grade import get_student_grade_by_work
from app.models import Lesson, LessonGrade, User
from app.models.schedule import LessonType
from app.services.attestation.deadline_validator import get_max_allowed_grade, validate_grade_for_max
from app.services.submission_journal_sync import journal_sync

logger = logging.getLogger(__name__)

_WORK_NUMBER_REQUIRED_TYPES = {LessonType.LAB, LessonType.PRACTICE}
_SUBMISSION_SYNC_TYPES = {LessonType.LAB, LessonType.PRACTICE}


class JournalGradeValidationError(ValueError):
    """Domain validation error for canonical grade writes."""


class JournalGradeConflictError(JournalGradeValidationError):
    """Legacy data conflict that blocks safe canonical writes."""


class JournalGradeWriteService:
    """Writes lesson grades under a single set of business rules."""

    async def list_cell_grades(self, db: AsyncSession, lesson_id: UUID, student_id: UUID) -> list[LessonGrade]:
        result = await db.execute(
            select(LessonGrade)
            .where(and_(LessonGrade.lesson_id == lesson_id, LessonGrade.student_id == student_id))
            .order_by(LessonGrade.updated_at.desc(), LessonGrade.created_at.desc())
        )
        return list(result.scalars().all())

    async def upsert_grade(
        self,
        db: AsyncSession,
        lesson: Lesson,
        student_id: UUID,
        grade: int,
        work_number: int | None,
        comment: str | None,
        actor_id: UUID,
        *,
        sync_submission: bool = True,
        submission_history: bool = True,
    ) -> LessonGrade:
        resolved_work_number = self._resolve_work_number(lesson, work_number)
        cell_grades = await self.list_cell_grades(db, lesson.id, student_id)
        if len(cell_grades) > 1:
            raise JournalGradeConflictError(self._conflict_message(lesson.id, student_id, cell_grades))
        existing = cell_grades[0] if cell_grades else None
        if (
            existing is not None
            and existing.work_number is not None
            and resolved_work_number is not None
            and existing.work_number != resolved_work_number
        ):
            raise JournalGradeValidationError(
                f"На этой паре у студента уже есть оценка за работу №{existing.work_number}. "
                "Вторая работа на одной паре запрещена."
            )
        return await self._write_grade(
            db,
            lesson=lesson,
            student_id=student_id,
            existing=existing,
            grade=grade,
            work_number=resolved_work_number,
            comment=comment,
            actor_id=actor_id,
            sync_submission=sync_submission,
            submission_history=submission_history,
        )

    async def write_grade(self, *args, **kwargs) -> LessonGrade:
        """Backward-compatible alias for upsert_grade()."""
        return await self.upsert_grade(*args, **kwargs)

    async def replace_grade(
        self,
        db: AsyncSession,
        existing: LessonGrade,
        grade: int,
        work_number: int | None,
        comment: str | None,
        actor_id: UUID,
        *,
        sync_submission: bool = True,
        submission_history: bool = True,
    ) -> LessonGrade:
        lesson = existing.lesson or await db.get(Lesson, existing.lesson_id)
        if lesson is None:
            raise JournalGradeValidationError("Занятие для оценки не найдено")

        cell_grades = await self.list_cell_grades(db, lesson.id, existing.student_id)
        if len(cell_grades) > 1:
            raise JournalGradeConflictError(self._conflict_message(lesson.id, existing.student_id, cell_grades))

        return await self._write_grade(
            db,
            lesson=lesson,
            student_id=existing.student_id,
            existing=existing,
            grade=grade,
            work_number=work_number,
            comment=comment,
            actor_id=actor_id,
            sync_submission=sync_submission,
            submission_history=submission_history,
        )

    async def update_grade(self, *args, **kwargs) -> LessonGrade:
        """Backward-compatible alias for replace_grade()."""
        return await self.replace_grade(*args, **kwargs)

    async def delete_grade(
        self,
        db: AsyncSession,
        grade: LessonGrade,
        actor_id: UUID | None = None,
        *,
        submission_history: bool = True,
    ) -> None:
        lesson = grade.lesson or await db.get(Lesson, grade.lesson_id)

        if lesson and grade.work_number is not None and lesson.lesson_type in _SUBMISSION_SYNC_TYPES:
            await journal_sync.rollback_from_journal(
                db,
                student_id=grade.student_id,
                lesson=lesson,
                work_number=grade.work_number,
                created_by=actor_id,
                append_history=submission_history,
            )

        await db.delete(grade)
        await db.flush()
        logger.info("Deleted grade lesson=%s student=%s work=%s", grade.lesson_id, grade.student_id, grade.work_number)

    async def _write_grade(
        self,
        db: AsyncSession,
        *,
        lesson: Lesson,
        student_id: UUID,
        existing: LessonGrade | None,
        grade: int,
        work_number: int | None,
        comment: str | None,
        actor_id: UUID,
        sync_submission: bool,
        submission_history: bool,
    ) -> LessonGrade:
        self._validate_lesson_write(lesson)
        await self._validate_student_membership(db, lesson, student_id)

        resolved_work_number = self._resolve_work_number(lesson, work_number)
        await self._validate_grade_limits(db, lesson, student_id, resolved_work_number, grade)

        previous_work_number = existing.work_number if existing else None
        merge_target = await self._find_merge_target(
            db,
            lesson=lesson,
            student_id=student_id,
            work_number=resolved_work_number,
            exclude_grade_id=existing.id if existing else None,
        )

        if existing is not None:
            grade_record = await self._replace_existing(
                db,
                lesson=lesson,
                existing=existing,
                merge_target=merge_target,
                grade=grade,
                work_number=resolved_work_number,
                comment=comment,
                actor_id=actor_id,
            )
        elif merge_target is not None and merge_target.lesson_id != lesson.id:
            merge_target.lesson_id = lesson.id
            merge_target.grade = grade
            merge_target.work_number = resolved_work_number
            merge_target.comment = comment
            if merge_target.created_by is None:
                merge_target.created_by = actor_id
            grade_record = merge_target
        else:
            grade_record = LessonGrade(
                lesson_id=lesson.id,
                student_id=student_id,
                work_number=resolved_work_number,
                grade=grade,
                comment=comment,
                created_by=actor_id,
            )
            db.add(grade_record)

        await db.flush()

        if sync_submission and lesson.lesson_type in _SUBMISSION_SYNC_TYPES and resolved_work_number is not None:
            await journal_sync.sync_from_journal(
                db,
                student_id=student_id,
                lesson=lesson,
                work_number=resolved_work_number,
                grade=grade,
                comment=comment,
                created_by=actor_id,
                append_history=submission_history,
            )

            if previous_work_number is not None and previous_work_number != resolved_work_number:
                await journal_sync.rollback_from_journal(
                    db,
                    student_id=student_id,
                    lesson=lesson,
                    work_number=previous_work_number,
                    created_by=actor_id,
                    append_history=submission_history,
                )

        logger.info(
            "Saved grade lesson=%s student=%s work=%s grade=%s",
            lesson.id,
            student_id,
            resolved_work_number,
            grade,
        )
        return grade_record

    async def _replace_existing(
        self,
        db: AsyncSession,
        *,
        lesson: Lesson,
        existing: LessonGrade,
        merge_target: LessonGrade | None,
        grade: int,
        work_number: int | None,
        comment: str | None,
        actor_id: UUID,
    ) -> LessonGrade:
        if merge_target is not None and merge_target.id != existing.id and merge_target.lesson_id != lesson.id:
            merge_target.lesson_id = lesson.id
            merge_target.grade = grade
            merge_target.work_number = work_number
            merge_target.comment = comment
            if merge_target.created_by is None:
                merge_target.created_by = actor_id
            await db.delete(existing)
            return merge_target

        existing.grade = grade
        existing.work_number = work_number
        existing.comment = comment
        return existing

    async def _find_merge_target(
        self,
        db: AsyncSession,
        *,
        lesson: Lesson,
        student_id: UUID,
        work_number: int | None,
        exclude_grade_id: UUID | None,
    ) -> LessonGrade | None:
        if work_number is None:
            return None
        return await get_student_grade_by_work(
            db,
            student_id=student_id,
            work_number=work_number,
            group_id=lesson.group_id,
            subject_id=lesson.subject_id,
            exclude_grade_id=exclude_grade_id,
        )

    async def _validate_grade_limits(
        self,
        db: AsyncSession,
        lesson: Lesson,
        student_id: UUID,
        work_number: int | None,
        grade: int,
    ) -> None:
        max_allowed = await get_max_allowed_grade(db, lesson, student_id=student_id, work_number=work_number)
        validate_grade_for_max(grade, max_allowed)

    async def _validate_student_membership(self, db: AsyncSession, lesson: Lesson, student_id: UUID) -> None:
        student = await db.get(User, student_id)
        if not student:
            raise JournalGradeValidationError("Студент не найден")
        if student.group_id != lesson.group_id:
            raise JournalGradeValidationError(f"Student {student_id} not in group {lesson.group_id}")
        if lesson.subgroup is not None and student.subgroup != lesson.subgroup:
            raise JournalGradeValidationError(f"Student {student_id} not in subgroup {lesson.subgroup}")

    def _validate_lesson_write(self, lesson: Lesson) -> None:
        if lesson.is_cancelled:
            raise JournalGradeValidationError("Нельзя выставлять оценки в отменённом занятии")

    def _resolve_work_number(self, lesson: Lesson, work_number: int | None) -> int | None:
        if lesson.lesson_type not in _WORK_NUMBER_REQUIRED_TYPES:
            return work_number

        resolved_work_number = work_number if work_number is not None else lesson.work_number
        if resolved_work_number is None:
            raise JournalGradeValidationError("Для lab/practice номер работы обязателен")
        return resolved_work_number

    def _conflict_message(self, lesson_id: UUID, student_id: UUID, grades: Iterable[LessonGrade]) -> str:
        return (
            f"Конфликт legacy-данных: у студента {student_id} уже {len(list(grades))} оценок "
            f"на занятии {lesson_id}. Сначала разрешите конфликт."
        )


journal_grade_service = JournalGradeWriteService()

__all__ = [
    "JournalGradeConflictError",
    "JournalGradeValidationError",
    "JournalGradeWriteService",
    "journal_grade_service",
]
