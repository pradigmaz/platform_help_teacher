"""Attendance query functions."""
from typing import Optional, List
from uuid import UUID
from datetime import date

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import Attendance


async def check_attendance_exists(
    db: AsyncSession,
    student_id: UUID,
    attendance_date: date
) -> Optional[Attendance]:
    """
    Проверка существования записи посещаемости для студента на дату.
    
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


async def get_attendance_by_student(
    db: AsyncSession,
    student_id: UUID,
    group_id: Optional[UUID] = None
) -> List[Attendance]:
    """
    Получение записей посещаемости студента.
    
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
