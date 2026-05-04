"""Atomic save flow for schedule lesson sheets."""

from collections import defaultdict
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Attendance, AttendanceStatus, Lesson, LessonGrade
from app.schemas.schedule import GroupedLectureSheetSaveRequest, LessonSheetSaveRequest
from app.services.grade_cell_summary import summarize_lesson_grade_cell
from app.services.journal_attendance_service import (
    JournalAttendanceValidationError,
    journal_attendance_service,
)
from app.services.journal_grade_service import (
    JournalGradeConflictError,
    JournalGradeValidationError,
    journal_grade_service,
)


class LessonSheetValidationError(ValueError):
    """Domain validation error for schedule lesson sheet saves."""


class LessonSheetService:
    """Coordinates lesson metadata, attendance and grades in one transaction."""

    async def save_grouped_sheet(
        self,
        db: AsyncSession,
        lessons_by_id: dict[UUID, Lesson],
        payload: GroupedLectureSheetSaveRequest,
        actor_id: UUID,
    ) -> dict:
        items = []
        for item in payload.items:
            lesson = lessons_by_id.get(item.lesson_id)
            if lesson is None:
                raise LessonSheetValidationError(f"Занятие {item.lesson_id} не найдено")

            sheet_payload = {
                "lesson_work_number": None,
                "status": payload.status,
                "attendance_updates": item.attendance_updates,
                "grade_updates": [],
            }
            if "topic" in payload.model_fields_set:
                sheet_payload["topic"] = payload.topic

            result = await self.save_sheet(
                db=db,
                lesson=lesson,
                payload=LessonSheetSaveRequest(**sheet_payload),
                actor_id=actor_id,
            )
            items.append(
                {
                    "lesson_id": lesson.id,
                    "attendance": result["attendance"],
                }
            )

        return {"items": items}

    async def save_sheet(
        self,
        db: AsyncSession,
        lesson: Lesson,
        payload: LessonSheetSaveRequest,
        actor_id: UUID,
    ) -> dict:
        target_is_cancelled = payload.status == "cancelled"
        target_ended_early = payload.status == "early"
        if target_is_cancelled and (payload.attendance_updates or payload.grade_updates):
            raise LessonSheetValidationError("Нельзя менять посещаемость или оценки при отмене занятия")

        if "topic" in payload.model_fields_set:
            lesson.topic = payload.topic
        if "lesson_work_number" in payload.model_fields_set:
            lesson.work_number = payload.lesson_work_number
        lesson.is_cancelled = target_is_cancelled
        lesson.ended_early = target_ended_early

        await self._apply_attendance_updates(db, lesson, payload, actor_id)
        await self._apply_grade_updates(db, lesson, payload, actor_id)
        await db.flush()

        return await self._build_response(db, lesson)

    async def _apply_attendance_updates(
        self,
        db: AsyncSession,
        lesson: Lesson,
        payload: LessonSheetSaveRequest,
        actor_id: UUID,
    ) -> None:
        updates_by_student: dict[UUID, str | None] = {}
        for update in payload.attendance_updates:
            updates_by_student[update.student_id] = update.status

        if not updates_by_student:
            return

        existing = await db.execute(
            select(Attendance).where(
                and_(Attendance.lesson_id == lesson.id, Attendance.student_id.in_(list(updates_by_student.keys())))
            )
        )
        existing_by_student = {record.student_id: record for record in existing.scalars().all()}

        to_upsert: list[tuple[UUID, AttendanceStatus]] = []
        for student_id, status in updates_by_student.items():
            current = existing_by_student.get(student_id)
            if status is None:
                if current is not None:
                    await db.delete(current)
                continue
            to_upsert.append((student_id, AttendanceStatus(status)))

        if not to_upsert:
            return

        try:
            await journal_attendance_service.bulk_upsert(
                db=db,
                lesson=lesson,
                records=to_upsert,
                actor_id=actor_id,
            )
        except JournalAttendanceValidationError as exc:
            raise LessonSheetValidationError(str(exc)) from exc

    async def _apply_grade_updates(
        self,
        db: AsyncSession,
        lesson: Lesson,
        payload: LessonSheetSaveRequest,
        actor_id: UUID,
    ) -> None:
        updates_by_student = {update.student_id: update for update in payload.grade_updates}
        if not updates_by_student:
            return

        existing = await db.execute(
            select(LessonGrade)
            .options()
            .where(
                and_(LessonGrade.lesson_id == lesson.id, LessonGrade.student_id.in_(list(updates_by_student.keys())))
            )
        )
        grades_by_student: dict[UUID, list[LessonGrade]] = defaultdict(list)
        for grade in existing.scalars().all():
            grades_by_student[grade.student_id].append(grade)

        for student_id, update in updates_by_student.items():
            existing_grades = grades_by_student.get(student_id, [])
            if update.grade is None:
                await self._delete_student_grade(db, lesson, existing_grades, update.work_number, actor_id)
                continue
            try:
                await journal_grade_service.upsert_grade(
                    db=db,
                    lesson=lesson,
                    student_id=student_id,
                    grade=update.grade,
                    work_number=update.work_number,
                    comment=None,
                    actor_id=actor_id,
                )
            except (JournalGradeValidationError, JournalGradeConflictError) as exc:
                raise LessonSheetValidationError(str(exc)) from exc

    async def _delete_student_grade(
        self,
        db: AsyncSession,
        lesson: Lesson,
        existing_grades: list[LessonGrade],
        work_number: int | None,
        actor_id: UUID,
    ) -> None:
        if not existing_grades:
            return

        if work_number is not None:
            existing_grades = [grade for grade in existing_grades if grade.work_number == work_number]

        if len(existing_grades) > 1:
            raise LessonSheetValidationError(
                f"Конфликт legacy-данных: у студента уже {len(existing_grades)} оценок на занятии {lesson.id}. "
                "Сначала разберите конфликт в журнале."
            )

        if existing_grades:
            await journal_grade_service.delete_grade(db, existing_grades[0], actor_id)

    async def _build_response(self, db: AsyncSession, lesson: Lesson) -> dict:
        attendance_result = await db.execute(select(Attendance).where(Attendance.lesson_id == lesson.id))
        grade_result = await db.execute(select(LessonGrade).where(LessonGrade.lesson_id == lesson.id))

        attendance = [
            {
                "student_id": record.student_id,
                "status": record.status.value if hasattr(record.status, "value") else record.status,
            }
            for record in attendance_result.scalars().all()
        ]

        grouped: dict[UUID, list[LessonGrade]] = defaultdict(list)
        for grade in grade_result.scalars().all():
            grouped[grade.student_id].append(grade)

        grades = []
        for student_id, items in grouped.items():
            grades.append(
                {
                    "student_id": student_id,
                    **summarize_lesson_grade_cell(items),
                }
            )

        return {
            "lesson": lesson,
            "attendance": attendance,
            "grades": grades,
        }


lesson_sheet_service = LessonSheetService()
