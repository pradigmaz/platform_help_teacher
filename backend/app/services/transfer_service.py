"""Сервис перевода студентов между группами/подгруппами"""

import logging
from datetime import date
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Activity,
    Attendance,
    AttendanceStatus,
    AttestationSettings,
    Group,
    Lesson,
    LessonGrade,
    StudentTransfer,
    User,
)
from app.models.attestation_settings import AttestationType
from app.models.schedule import LessonType
from app.schemas.transfer import (
    AttendanceSnapshot,
    LabGradeSnapshot,
    StudentTransfersResponse,
    TransferRequest,
    TransferResponse,
    TransferSummary,
)
from app.services.attendance_slots import build_attendance_slot_filter, get_lesson_slot_sets, matches_attendance_slot
from app.services.attestation.lab_progress import dedupe_lesson_grade_rows
from app.services.schedule_constants import today_msk

logger = logging.getLogger(__name__)


class TransferService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _validate_attestation_period(self, attestation_type: AttestationType) -> None:
        """
        Проверка, что период аттестации ещё не завершён.

        Raises:
            ValueError: Если period_end_date аттестации уже прошла.
        """
        settings_query = select(AttestationSettings).where(AttestationSettings.attestation_type == attestation_type)
        result = await self.db.execute(settings_query)
        settings = result.scalar_one_or_none()

        if settings and settings.period_end_date:
            today = today_msk()
            if settings.period_end_date < today:
                raise ValueError(
                    f"Период аттестации '{attestation_type.value}' завершён "
                    f"({settings.period_end_date}). Перевод невозможен."
                )

    async def create_transfer(
        self, student_id: UUID, request: TransferRequest, created_by_id: UUID | None = None
    ) -> TransferResponse:
        """Создать перевод студента с сохранением снапшота."""

        # Валидация: период аттестации не должен быть завершён
        await self._validate_attestation_period(AttestationType(request.attestation_type.value))

        # Получаем студента
        student = await self.db.get(User, student_id)
        if not student:
            raise ValueError(f"Студент {student_id} не найден")

        from_group_id = student.group_id
        from_subgroup = student.subgroup
        transfer_date = request.transfer_date or today_msk()

        # Получаем группы для имён
        from_group = await self.db.get(Group, from_group_id) if from_group_id else None
        to_group = await self.db.get(Group, request.to_group_id)

        if not to_group:
            raise ValueError(f"Целевая группа {request.to_group_id} не найдена")

        # Создаём снапшот данных студента
        attendance_data = await self._create_attendance_snapshot(
            student_id, from_group_id, from_subgroup, request.attestation_type
        )
        lab_grades_data = await self._create_lab_grades_snapshot(student_id, from_group_id, request.attestation_type)
        activity_points = await self._get_activity_points(student_id, request.attestation_type)

        # Создаём запись перевода
        transfer = StudentTransfer(
            student_id=student_id,
            from_group_id=from_group_id,
            from_subgroup=from_subgroup,
            to_group_id=request.to_group_id,
            to_subgroup=request.to_subgroup,
            transfer_date=transfer_date,
            attestation_type=AttestationType(request.attestation_type.value),
            attendance_data=attendance_data.model_dump(),
            lab_grades_data=[g.model_dump() for g in lab_grades_data],
            activity_points=activity_points,
            created_by_id=created_by_id,
        )
        self.db.add(transfer)

        # Обновляем студента
        student.group_id = request.to_group_id
        student.subgroup = request.to_subgroup

        await self.db.commit()
        await self.db.refresh(transfer)

        logger.info(
            f"Перевод студента {student.full_name}: "
            f"{from_group.name if from_group else 'N/A'} (п/г {from_subgroup}) -> "
            f"{to_group.name} (п/г {request.to_subgroup})"
        )

        return TransferResponse(
            id=transfer.id,
            student_id=student_id,
            student_name=student.full_name,
            from_group_id=from_group_id,
            from_group_name=from_group.name if from_group else None,
            from_subgroup=from_subgroup,
            to_group_id=request.to_group_id,
            to_group_name=to_group.name,
            to_subgroup=request.to_subgroup,
            transfer_date=transfer_date,
            attestation_type=request.attestation_type,
            attendance_data=attendance_data,
            lab_grades_data=lab_grades_data,
            activity_points=activity_points,
            created_at=transfer.created_at.isoformat(),
        )

    async def _create_attendance_snapshot(
        self, student_id: UUID, group_id: UUID | None, subgroup: int | None, attestation_type
    ) -> AttendanceSnapshot:
        """Создать снапшот посещаемости с учётом подгруппы."""
        if not group_id:
            return AttendanceSnapshot()

        # Получаем период аттестации
        from app.models import AttestationSettings

        settings_query = select(AttestationSettings).where(
            AttestationSettings.attestation_type == attestation_type.value
        )
        result = await self.db.execute(settings_query)
        settings = result.scalar_one_or_none()

        # Получаем релевантные занятия
        lessons_query = select(Lesson).where(Lesson.group_id == group_id, Lesson.is_cancelled.is_(False))
        if settings and settings.period_start_date:
            lessons_query = lessons_query.where(Lesson.date >= settings.period_start_date)
        if settings and settings.period_end_date:
            lessons_query = lessons_query.where(Lesson.date <= settings.period_end_date)

        # Фильтр по подгруппе
        if subgroup is not None:
            lessons_query = lessons_query.where(or_(Lesson.subgroup.is_(None), Lesson.subgroup == subgroup))
        else:
            lessons_query = lessons_query.where(Lesson.subgroup.is_(None))

        lessons_result = await self.db.execute(lessons_query)
        relevant_lessons = list(lessons_result.scalars().all())

        if not relevant_lessons:
            return AttendanceSnapshot(total_lessons=0)

        # Получаем посещаемость
        slot_filter = build_attendance_slot_filter(relevant_lessons)
        attendance_query = select(Attendance).where(
            Attendance.student_id == student_id,
            Attendance.group_id == group_id,
            slot_filter,
        )
        attendance_result = await self.db.execute(attendance_query)
        records = list(attendance_result.scalars().all())

        present = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
        late = sum(1 for r in records if r.status == AttendanceStatus.LATE)
        excused = sum(1 for r in records if r.status == AttendanceStatus.EXCUSED)
        absent = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)

        subject_snapshots: dict[str, dict[str, int | float]] = {}
        lessons_by_subject: dict[str, list[Lesson]] = {}
        for lesson in relevant_lessons:
            if lesson.subject_id is None:
                continue
            lessons_by_subject.setdefault(str(lesson.subject_id), []).append(lesson)

        for subject_id, subject_lessons in lessons_by_subject.items():
            lesson_ids, legacy_slots = get_lesson_slot_sets(subject_lessons)
            subject_records = [
                record
                for record in records
                if matches_attendance_slot(record, lesson_ids=lesson_ids, legacy_slots=legacy_slots)
            ]
            subject_snapshots[subject_id] = {
                "total_lessons": len(subject_lessons),
                "present": sum(1 for r in subject_records if r.status == AttendanceStatus.PRESENT),
                "late": sum(1 for r in subject_records if r.status == AttendanceStatus.LATE),
                "excused": sum(1 for r in subject_records if r.status == AttendanceStatus.EXCUSED),
                "absent": sum(1 for r in subject_records if r.status == AttendanceStatus.ABSENT),
                "activity_points": 0.0,
            }

        if subject_snapshots:
            activity_query = (
                select(Activity.subject_id, func.sum(Activity.points))
                .where(
                    Activity.student_id == student_id,
                    Activity.attestation_type == attestation_type.value,
                    Activity.is_active,
                )
                .group_by(Activity.subject_id)
            )
            activity_result = await self.db.execute(activity_query)
            single_subject_key = next(iter(subject_snapshots)) if len(subject_snapshots) == 1 else None
            for activity_subject_id, points in activity_result.all():
                target_subject_key = str(activity_subject_id) if activity_subject_id else single_subject_key
                if target_subject_key and target_subject_key in subject_snapshots:
                    subject_snapshots[target_subject_key]["activity_points"] = float(points or 0.0)

        return AttendanceSnapshot(
            total_lessons=len(relevant_lessons),
            present=present,
            late=late,
            excused=excused,
            absent=absent,
            subjects=subject_snapshots,
        )

    async def _create_lab_grades_snapshot(
        self, student_id: UUID, group_id: UUID | None, attestation_type
    ) -> list[LabGradeSnapshot]:
        """Создать снапшот оценок за лабы."""
        if not group_id:
            return []

        # Получаем период
        from app.models import AttestationSettings

        settings_query = select(AttestationSettings).where(
            AttestationSettings.attestation_type == attestation_type.value
        )
        result = await self.db.execute(settings_query)
        settings = result.scalar_one_or_none()

        # Получаем оценки
        grades_query = (
            select(LessonGrade, Lesson.subject_id)
            .join(Lesson, LessonGrade.lesson_id == Lesson.id)
            .where(LessonGrade.student_id == student_id)
            .where(Lesson.group_id == group_id)
            .where(LessonGrade.work_number.isnot(None))
            .where(Lesson.is_cancelled.is_(False))
            .where(Lesson.lesson_type.in_((LessonType.LAB, LessonType.PRACTICE)))
        )
        if settings and settings.period_start_date:
            grades_query = grades_query.where(Lesson.date >= settings.period_start_date)
        if settings and settings.period_end_date:
            grades_query = grades_query.where(Lesson.date <= settings.period_end_date)

        grades_result = await self.db.execute(grades_query)
        rows = grades_result.all()
        grades = dedupe_lesson_grade_rows(rows)
        subject_by_grade_id = {grade.id: subject_id for grade, subject_id in rows}

        return [
            LabGradeSnapshot(
                subject_id=str(subject_by_grade_id.get(g.id)) if subject_by_grade_id.get(g.id) else None,
                work_number=g.work_number or 0,
                grade=g.grade,
                lesson_id=str(g.lesson_id) if g.lesson_id else None,
            )
            for g in grades
        ]

    async def _get_activity_points(self, student_id: UUID, attestation_type) -> float:
        """Получить сумму баллов активности."""
        query = select(func.sum(Activity.points)).where(
            Activity.student_id == student_id, Activity.attestation_type == attestation_type.value, Activity.is_active
        )
        result = await self.db.execute(query)
        return result.scalar() or 0.0

    async def get_student_transfers(self, student_id: UUID) -> StudentTransfersResponse:
        """Получить историю переводов студента."""
        student = await self.db.get(User, student_id)
        if not student:
            raise ValueError(f"Студент {student_id} не найден")

        query = (
            select(StudentTransfer)
            .options(selectinload(StudentTransfer.from_group), selectinload(StudentTransfer.to_group))
            .where(StudentTransfer.student_id == student_id)
            .order_by(StudentTransfer.transfer_date.desc())
        )
        result = await self.db.execute(query)
        transfers = list(result.scalars().all())

        return StudentTransfersResponse(
            student_id=student_id,
            student_name=student.full_name,
            transfers=[
                TransferSummary(
                    id=t.id,
                    from_group_name=t.from_group.name if t.from_group else None,
                    from_subgroup=t.from_subgroup,
                    to_group_name=t.to_group.name if t.to_group else None,
                    to_subgroup=t.to_subgroup,
                    transfer_date=t.transfer_date,
                    attestation_type=t.attestation_type.value,
                )
                for t in transfers
            ],
        )

    async def get_transfers_in_period(
        self, student_id: UUID, attestation_type: str, period_start: date | None = None, period_end: date | None = None
    ) -> list[StudentTransfer]:
        """Получить переводы студента в периоде аттестации."""
        query = select(StudentTransfer).where(
            StudentTransfer.student_id == student_id, StudentTransfer.attestation_type == attestation_type
        )
        if period_start:
            query = query.where(StudentTransfer.transfer_date >= period_start)
        if period_end:
            query = query.where(StudentTransfer.transfer_date <= period_end)

        query = query.order_by(StudentTransfer.transfer_date.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
