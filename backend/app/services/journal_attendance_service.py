"""Unified write-path for journal attendance."""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import upsert_attendance
from app.crud.attendance import AttendanceValidationError, DuplicateAttendanceError, FutureDateError
from app.models import Attendance, AttendanceStatus, Lesson, User
from app.models.attendance import LessonType as AttendanceLessonType

logger = logging.getLogger(__name__)


class JournalAttendanceValidationError(ValueError):
    """Domain validation error for canonical attendance writes."""


JournalAttendanceError = JournalAttendanceValidationError


class JournalAttendanceService:
    """Writes attendance through shared CRUD validation and lesson context."""

    async def bulk_upsert(
        self,
        db: AsyncSession,
        lesson: Lesson,
        records: list[tuple[UUID, AttendanceStatus]],
        actor_id: UUID,
    ) -> list[Attendance]:
        if lesson.is_cancelled:
            raise JournalAttendanceValidationError("Нельзя отмечать посещаемость в отменённом занятии")

        updated: list[Attendance] = []
        for student_id, status in records:
            await self._validate_student_membership(db, lesson, student_id)
            try:
                attendance = await upsert_attendance(
                    db=db,
                    student_id=student_id,
                    group_id=lesson.group_id,
                    attendance_date=lesson.date,
                    status=status,
                    created_by=actor_id,
                    lesson_number=lesson.lesson_number,
                )
            except (AttendanceValidationError, DuplicateAttendanceError, FutureDateError) as exc:
                raise JournalAttendanceValidationError(str(exc)) from exc

            attendance.lesson_id = lesson.id
            attendance.lesson_type = AttendanceLessonType(lesson.lesson_type.value)
            attendance.subgroup = lesson.subgroup
            updated.append(attendance)

        await db.flush()
        logger.info("Bulk upserted %s attendance records for lesson %s", len(updated), lesson.id)
        return updated

    async def bulk_upsert_attendance(self, *args, **kwargs) -> list[Attendance]:
        """Backward-compatible alias for bulk_upsert()."""
        return await self.bulk_upsert(*args, **kwargs)

    async def _validate_student_membership(self, db: AsyncSession, lesson: Lesson, student_id: UUID) -> None:
        student = await db.get(User, student_id)
        if not student:
            raise JournalAttendanceValidationError("Студент не найден")
        if student.group_id != lesson.group_id:
            raise JournalAttendanceValidationError(f"Student {student_id} not in group {lesson.group_id}")
        if lesson.subgroup is not None and student.subgroup != lesson.subgroup:
            raise JournalAttendanceValidationError(f"Student {student_id} not in subgroup {lesson.subgroup}")


journal_attendance_service = JournalAttendanceService()

__all__ = [
    "JournalAttendanceError",
    "JournalAttendanceService",
    "JournalAttendanceValidationError",
    "journal_attendance_service",
]
