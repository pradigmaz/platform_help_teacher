"""Attendance CRUD operations."""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.attendance import Attendance, AttendanceStatus
from .exceptions import (
    AttendanceValidationError,
    DuplicateAttendanceError,
    FutureDateError,
)
from .validators import validate_student_in_group
from .queries import check_attendance_exists

logger = logging.getLogger(__name__)


async def create_attendance(
    db: AsyncSession,
    student_id: UUID,
    group_id: UUID,
    attendance_date: date,
    status: AttendanceStatus,
    created_by: Optional[UUID] = None
) -> Attendance:
    """
    Создание записи посещаемости с валидацией.
    
    Args:
        db: Сессия базы данных
        student_id: ID студента
        group_id: ID группы
        attendance_date: Дата занятия
        status: Статус посещаемости
        created_by: ID создателя записи
        
    Returns:
        Attendance: Созданная запись
        
    Raises:
        StudentNotFoundError: Если студент не найден
        StudentNotInGroupError: Если студент не принадлежит группе
        DuplicateAttendanceError: Если запись уже существует
        FutureDateError: Если дата в будущем
    """
    await validate_student_in_group(db, student_id, group_id)
    
    if attendance_date > date.today():
        raise FutureDateError(f"Нельзя создать запись для будущей даты {attendance_date}")
    
    existing = await check_attendance_exists(db, student_id, attendance_date)
    if existing:
        raise DuplicateAttendanceError(
            f"Запись для студента {student_id} на {attendance_date} уже существует"
        )
    
    attendance = Attendance(
        student_id=student_id,
        group_id=group_id,
        date=attendance_date,
        status=status,
        created_by=created_by
    )
    db.add(attendance)
    
    try:
        async with db.begin_nested():
            await db.flush()
    except IntegrityError as e:
        if "uq_attendance_student_date" in str(e):
            raise DuplicateAttendanceError(
                f"Запись для студента {student_id} на {attendance_date} уже существует"
            )
        raise
    
    logger.info(f"Created attendance: student={student_id}, date={attendance_date}, status={status}")
    return attendance



async def update_attendance(
    db: AsyncSession,
    attendance_id: UUID,
    status: AttendanceStatus
) -> Optional[Attendance]:
    """
    Обновление статуса посещаемости.
    
    Args:
        db: Сессия базы данных
        attendance_id: ID записи посещаемости
        status: Новый статус
        
    Returns:
        Attendance или None если запись не найдена
    """
    query = select(Attendance).where(Attendance.id == attendance_id)
    result = await db.execute(query)
    attendance = result.scalar_one_or_none()
    
    if not attendance:
        return None
    
    attendance.status = status
    await db.flush()
    
    logger.info(f"Updated attendance {attendance_id} to status {status}")
    return attendance


async def upsert_attendance(
    db: AsyncSession,
    student_id: UUID,
    group_id: UUID,
    attendance_date: date,
    status: AttendanceStatus,
    created_by: Optional[UUID] = None
) -> Attendance:
    """
    Создание или обновление записи посещаемости.
    
    Args:
        db: Сессия базы данных
        student_id: ID студента
        group_id: ID группы
        attendance_date: Дата занятия
        status: Статус посещаемости
        created_by: ID создателя записи
        
    Returns:
        Attendance: Созданная или обновлённая запись
    """
    existing = await check_attendance_exists(db, student_id, attendance_date)
    
    if existing:
        existing.status = status
        await db.flush()
        logger.info(f"Updated attendance: student={student_id}, date={attendance_date}, status={status}")
        return existing
    
    return await create_attendance(
        db=db,
        student_id=student_id,
        group_id=group_id,
        attendance_date=attendance_date,
        status=status,
        created_by=created_by
    )


async def delete_attendance(
    db: AsyncSession,
    attendance_id: UUID
) -> bool:
    """
    Удаление записи посещаемости.
    
    Args:
        db: Сессия базы данных
        attendance_id: ID записи
        
    Returns:
        bool: True если запись удалена, False если не найдена
    """
    query = select(Attendance).where(Attendance.id == attendance_id)
    result = await db.execute(query)
    attendance = result.scalar_one_or_none()
    
    if not attendance:
        return False
    
    await db.delete(attendance)
    await db.flush()
    
    logger.info(f"Deleted attendance record {attendance_id}")
    return True


async def bulk_create_attendance(
    db: AsyncSession,
    group_id: UUID,
    attendance_date: date,
    student_statuses: List[tuple[UUID, AttendanceStatus]],
    created_by: Optional[UUID] = None
) -> List[Attendance]:
    """
    Массовое создание записей посещаемости для группы.
    
    Args:
        db: Сессия базы данных
        group_id: ID группы
        attendance_date: Дата занятия
        student_statuses: Список кортежей (student_id, status)
        created_by: ID создателя записей
        
    Returns:
        List[Attendance]: Список созданных записей
    """
    created_records = []
    
    for student_id, status in student_statuses:
        try:
            async with db.begin_nested():
                attendance = await upsert_attendance(
                    db=db,
                    student_id=student_id,
                    group_id=group_id,
                    attendance_date=attendance_date,
                    status=status,
                    created_by=created_by
                )
                created_records.append(attendance)
        except (AttendanceValidationError, IntegrityError) as e:
            logger.warning(f"Skipping attendance for student {student_id}: {e}")
            continue
    
    return created_records
