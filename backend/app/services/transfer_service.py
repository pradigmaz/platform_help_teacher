"""Сервис перевода студентов между группами/подгруппами"""
import logging
from typing import Optional, List
from datetime import date, datetime, timezone
from uuid import UUID
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    User, Group, Lesson, Attendance, AttendanceStatus,
    LessonGrade, Activity, StudentTransfer, AttestationSettings
)
from app.models.attestation_settings import AttestationType
from app.schemas.transfer import (
    TransferRequest, TransferResponse, TransferSummary,
    AttendanceSnapshot, LabGradeSnapshot, StudentTransfersResponse
)

logger = logging.getLogger(__name__)


class TransferService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _validate_attestation_period(
        self,
        attestation_type: AttestationType
    ) -> None:
        """
        Проверка, что период аттестации ещё не завершён.
        
        Raises:
            ValueError: Если period_end_date аттестации уже прошла.
        """
        settings_query = select(AttestationSettings).where(
            AttestationSettings.attestation_type == attestation_type
        )
        result = await self.db.execute(settings_query)
        settings = result.scalar_one_or_none()
        
        if settings and settings.period_end_date:
            today = datetime.now(timezone.utc).date()
            if settings.period_end_date < today:
                raise ValueError(
                    f"Период аттестации '{attestation_type.value}' завершён "
                    f"({settings.period_end_date}). Перевод невозможен."
                )

    async def create_transfer(
        self,
        student_id: UUID,
        request: TransferRequest,
        created_by_id: Optional[UUID] = None
    ) -> TransferResponse:
        """Создать перевод студента с сохранением снапшота."""
        
        # Валидация: период аттестации не должен быть завершён
        await self._validate_attestation_period(
            AttestationType(request.attestation_type.value)
        )
        
        # Получаем студента
        student = await self.db.get(User, student_id)
        if not student:
            raise ValueError(f"Студент {student_id} не найден")
        
        from_group_id = student.group_id
        from_subgroup = student.subgroup
        transfer_date = request.transfer_date or date.today()
        
        # Получаем группы для имён
        from_group = await self.db.get(Group, from_group_id) if from_group_id else None
        to_group = await self.db.get(Group, request.to_group_id)
        
        if not to_group:
            raise ValueError(f"Целевая группа {request.to_group_id} не найдена")
        
        # Создаём снапшот данных студента
        attendance_data = await self._create_attendance_snapshot(
            student_id, from_group_id, from_subgroup, request.attestation_type
        )
        lab_grades_data = await self._create_lab_grades_snapshot(
            student_id, from_group_id, request.attestation_type
        )
        activity_points = await self._get_activity_points(
            student_id, request.attestation_type
        )
        
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
            created_by_id=created_by_id
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
            created_at=transfer.created_at.isoformat()
        )

    async def _create_attendance_snapshot(
        self,
        student_id: UUID,
        group_id: Optional[UUID],
        subgroup: Optional[int],
        attestation_type
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
        lessons_query = select(Lesson).where(Lesson.group_id == group_id)
        if settings and settings.period_start_date:
            lessons_query = lessons_query.where(Lesson.date >= settings.period_start_date)
        if settings and settings.period_end_date:
            lessons_query = lessons_query.where(Lesson.date <= settings.period_end_date)
        
        # Фильтр по подгруппе
        if subgroup is not None:
            lessons_query = lessons_query.where(
                or_(Lesson.subgroup.is_(None), Lesson.subgroup == subgroup)
            )
        else:
            lessons_query = lessons_query.where(Lesson.subgroup.is_(None))
        
        lessons_result = await self.db.execute(lessons_query)
        relevant_lessons = list(lessons_result.scalars().all())
        relevant_dates = {l.date for l in relevant_lessons}
        
        if not relevant_dates:
            return AttendanceSnapshot(total_lessons=0)
        
        # Получаем посещаемость
        attendance_query = select(Attendance).where(
            Attendance.student_id == student_id,
            Attendance.group_id == group_id,
            Attendance.date.in_(relevant_dates)
        )
        attendance_result = await self.db.execute(attendance_query)
        records = list(attendance_result.scalars().all())
        
        present = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
        late = sum(1 for r in records if r.status == AttendanceStatus.LATE)
        excused = sum(1 for r in records if r.status == AttendanceStatus.EXCUSED)
        absent = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
        
        return AttendanceSnapshot(
            total_lessons=len(relevant_lessons),
            present=present,
            late=late,
            excused=excused,
            absent=absent
        )

    async def _create_lab_grades_snapshot(
        self,
        student_id: UUID,
        group_id: Optional[UUID],
        attestation_type
    ) -> List[LabGradeSnapshot]:
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
            select(LessonGrade)
            .join(Lesson, LessonGrade.lesson_id == Lesson.id)
            .where(LessonGrade.student_id == student_id)
        )
        if settings and settings.period_start_date:
            grades_query = grades_query.where(Lesson.date >= settings.period_start_date)
        if settings and settings.period_end_date:
            grades_query = grades_query.where(Lesson.date <= settings.period_end_date)
        
        grades_result = await self.db.execute(grades_query)
        grades = list(grades_result.scalars().all())
        
        return [
            LabGradeSnapshot(
                work_number=g.work_number or 0,
                grade=g.grade,
                lesson_id=str(g.lesson_id) if g.lesson_id else None
            )
            for g in grades
        ]

    async def _get_activity_points(
        self,
        student_id: UUID,
        attestation_type
    ) -> float:
        """Получить сумму баллов активности."""
        query = select(func.sum(Activity.points)).where(
            Activity.student_id == student_id,
            Activity.attestation_type == attestation_type.value,
            Activity.is_active == True
        )
        result = await self.db.execute(query)
        return result.scalar() or 0.0

    async def get_student_transfers(
        self,
        student_id: UUID
    ) -> StudentTransfersResponse:
        """Получить историю переводов студента."""
        student = await self.db.get(User, student_id)
        if not student:
            raise ValueError(f"Студент {student_id} не найден")
        
        query = (
            select(StudentTransfer)
            .options(
                selectinload(StudentTransfer.from_group),
                selectinload(StudentTransfer.to_group)
            )
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
                    attestation_type=t.attestation_type.value
                )
                for t in transfers
            ]
        )

    async def get_transfers_in_period(
        self,
        student_id: UUID,
        attestation_type: str,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None
    ) -> List[StudentTransfer]:
        """Получить переводы студента в периоде аттестации."""
        query = (
            select(StudentTransfer)
            .where(
                StudentTransfer.student_id == student_id,
                StudentTransfer.attestation_type == attestation_type
            )
        )
        if period_start:
            query = query.where(StudentTransfer.transfer_date >= period_start)
        if period_end:
            query = query.where(StudentTransfer.transfer_date <= period_end)
        
        query = query.order_by(StudentTransfer.transfer_date.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
