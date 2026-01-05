"""
CRUD операции для модели Attendance.

Реализует Requirements:
- 8.1: store attendance records with student, group, date, and status
- 8.2: support attendance status types: PRESENT, ABSENT, LATE, EXCUSED
- 8.3: validate student belongs to specified group (WHEN storing attendance)
- 8.4: prevent duplicate attendance records for same student and date
- 8.5: provide efficient querying of attendance data for calculations
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import date

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.attendance import Attendance, AttendanceStatus
from app.models.user import User

logger = logging.getLogger(__name__)


class AttendanceValidationError(Exception):
    """Ошибка валидации данных посещаемости"""
    pass


class DuplicateAttendanceError(AttendanceValidationError):
    """Ошибка: дублирующая запись посещаемости"""
    pass


class StudentNotInGroupError(AttendanceValidationError):
    """Ошибка: студент не принадлежит указанной группе"""
    pass


class StudentNotFoundError(AttendanceValidationError):
    """Ошибка: студент не найден"""
    pass


class FutureDateError(AttendanceValidationError):
    """Ошибка: дата посещаемости в будущем"""
    pass


async def validate_student_in_group(
    db: AsyncSession,
    student_id: UUID,
    group_id: UUID
) -> User:
    """
    Проверка принадлежности студента к группе.
    
    Requirements: 8.3 - validate student belongs to specified group
    
    Args:
        db: Сессия базы данных
        student_id: ID студента
        group_id: ID группы
        
    Returns:
        User: Объект студента
        
    Raises:
        StudentNotFoundError: Если студент не найден
        StudentNotInGroupError: Если студент не принадлежит группе
    """
    query = select(User).where(User.id == student_id)
    result = await db.execute(query)
    student = result.scalar_one_or_none()
    
    if not student:
        raise StudentNotFoundError(f"Студент с ID {student_id} не найден")
    
    if student.group_id != group_id:
        raise StudentNotInGroupError(
            f"Студент {student_id} не принадлежит группе {group_id}. "
            f"Текущая группа студента: {student.group_id}"
        )
    
    return student


async def check_attendance_exists(
    db: AsyncSession,
    student_id: UUID,
    attendance_date: date
) -> Optional[Attendance]:
    """
    Проверка существования записи посещаемости для студента на дату.
    
    Requirements: 8.4 - prevent duplicate attendance records
    
    Args:
        db: Сессия базы данных
        student_id: ID студента
        attendance_date: Дата занятия
        
    Returns:
        Attendance или None если запись не существует
    """
    query = select(Attendance).where(
        and_(
            Attendance.student_id == student_id,
            Attendance.date == attendance_date
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


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
    
    Requirements:
    - 8.1: store attendance records with student, group, date, and status
    - 8.3: validate student belongs to specified group
    - 8.4: prevent duplicate attendance records
    
    Args:
        db: Сессия базы данных
        student_id: ID студента
        group_id: ID группы
        attendance_date: Дата занятия
        status: Статус посещаемости
        created_by: ID создателя записи (преподаватель)
        
    Returns:
        Attendance: Созданная запись
        
    Raises:
        StudentNotFoundError: Если студент не найден
        StudentNotInGroupError: Если студент не принадлежит группе
        DuplicateAttendanceError: Если запись уже существует
    """
    # Валидация принадлежности студента к группе (Requirements 8.3)
    await validate_student_in_group(db, student_id, group_id)
    
    # Валидация даты (не в будущем)
    if attendance_date > date.today():
        raise FutureDateError(f"Нельзя создать запись посещаемости для будущей даты {attendance_date}")
    
    # Проверка на дубликат (Requirements 8.4)
    existing = await check_attendance_exists(db, student_id, attendance_date)
    if existing:
        raise DuplicateAttendanceError(
            f"Запись посещаемости для студента {student_id} на дату {attendance_date} уже существует"
        )
    
    # Создание записи (Requirements 8.1)
    attendance = Attendance(
        student_id=student_id,
        group_id=group_id,
        date=attendance_date,
        status=status,
        created_by=created_by
    )
    
    db.add(attendance)
    
    try:
        # Используем savepoint для безопасной обработки ошибок constraint
        async with db.begin_nested():
            await db.flush()
    except IntegrityError as e:
        # Обработка constraint violation на уровне БД
        if "uq_attendance_student_date" in str(e):
            raise DuplicateAttendanceError(
                f"Запись посещаемости для студента {student_id} на дату {attendance_date} уже существует"
            )
        raise
    
    logger.info(f"Created attendance record: student={student_id}, date={attendance_date}, status={status}")
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
    
    Если запись существует - обновляет статус.
    Если не существует - создаёт новую с валидацией.
    
    Args:
        db: Сессия базы данных
        student_id: ID студента
        group_id: ID группы
        attendance_date: Дата занятия
        status: Статус посещаемости
        created_by: ID создателя записи
        
    Returns:
        Attendance: Созданная или обновлённая запись
        
    Raises:
        StudentNotFoundError: Если студент не найден
        StudentNotInGroupError: Если студент не принадлежит группе
    """
    # Проверяем существование записи
    existing = await check_attendance_exists(db, student_id, attendance_date)
    
    if existing:
        # Обновляем существующую запись
        existing.status = status
        await db.flush()
        logger.info(f"Updated attendance: student={student_id}, date={attendance_date}, status={status}")
        return existing
    
    # Создаём новую запись с валидацией
    return await create_attendance(
        db=db,
        student_id=student_id,
        group_id=group_id,
        attendance_date=attendance_date,
        status=status,
        created_by=created_by
    )


async def get_attendance_by_student(
    db: AsyncSession,
    student_id: UUID,
    group_id: Optional[UUID] = None
) -> List[Attendance]:
    """
    Получение записей посещаемости студента.
    
    Requirements: 8.5 - efficient querying of attendance data
    
    Args:
        db: Сессия базы данных
        student_id: ID студента
        group_id: ID группы (опционально для фильтрации)
        
    Returns:
        List[Attendance]: Список записей посещаемости
    """
    conditions = [Attendance.student_id == student_id]
    
    if group_id:
        conditions.append(Attendance.group_id == group_id)
    
    query = select(Attendance).where(and_(*conditions)).order_by(Attendance.date.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_attendance_by_group_and_date(
    db: AsyncSession,
    group_id: UUID,
    attendance_date: date
) -> List[Attendance]:
    """
    Получение записей посещаемости группы на дату.
    
    Requirements: 8.5 - efficient querying (использует индекс idx_attendance_group_date)
    
    Args:
        db: Сессия базы данных
        group_id: ID группы
        attendance_date: Дата занятия
        
    Returns:
        List[Attendance]: Список записей посещаемости
    """
    query = select(Attendance).where(
        and_(
            Attendance.group_id == group_id,
            Attendance.date == attendance_date
        )
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_attendance_by_group_date_range(
    db: AsyncSession,
    group_id: UUID,
    start_date: date,
    end_date: date
) -> List[Attendance]:
    """
    Получение записей посещаемости группы за период.
    
    Requirements: 8.5 - efficient querying for calculations
    
    Args:
        db: Сессия базы данных
        group_id: ID группы
        start_date: Начало периода
        end_date: Конец периода
        
    Returns:
        List[Attendance]: Список записей посещаемости
    """
    query = select(Attendance).where(
        and_(
            Attendance.group_id == group_id,
            Attendance.date >= start_date,
            Attendance.date <= end_date
        )
    ).order_by(Attendance.date)
    result = await db.execute(query)
    return list(result.scalars().all())


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
    
    Валидирует каждого студента и пропускает дубликаты.
    
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
        # Используем savepoint для каждой записи, чтобы ошибка в одной не отменяла остальные
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
