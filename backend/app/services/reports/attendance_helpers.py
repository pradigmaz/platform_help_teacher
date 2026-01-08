"""
Хелперы для сбора данных посещаемости.
"""
from typing import List, Dict
from uuid import UUID
from collections import defaultdict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import Attendance
from app.models.user import User
from app.schemas.report import AttendanceDistribution, AttendanceRecord


async def get_group_attendance_stats(
    db: AsyncSession,
    group_id: UUID,
    students: List[User]
) -> Dict[UUID, Dict]:
    """Получить статистику посещаемости группы."""
    student_ids = [s.id for s in students]
    
    query = (
        select(
            Attendance.student_id,
            Attendance.status,
            func.count(Attendance.id).label('count')
        )
        .where(
            Attendance.group_id == group_id,
            Attendance.student_id.in_(student_ids)
        )
        .group_by(Attendance.student_id, Attendance.status)
    )
    result = await db.execute(query)
    
    stats = defaultdict(lambda: {'present': 0, 'late': 0, 'excused': 0, 'absent': 0, 'total': 0})
    for row in result.all():
        status_str = row.status.value.lower() if hasattr(row.status, 'value') else str(row.status).lower()
        stats[row.student_id][status_str] = row.count
        stats[row.student_id]['total'] += row.count
    
    for student_id, data in stats.items():
        total = data['total']
        if total > 0:
            present_equivalent = data['present'] + data['late'] * 0.5 + data['excused'] * 0.5
            data['rate'] = round(present_equivalent / total * 100, 1)
        else:
            data['rate'] = 0.0
    
    return dict(stats)


async def get_attendance_distribution(
    db: AsyncSession,
    group_id: UUID,
    students: List[User]
) -> AttendanceDistribution:
    """Получить распределение посещаемости группы."""
    student_ids = [s.id for s in students]
    
    query = (
        select(Attendance.status, func.count(Attendance.id).label('count'))
        .where(
            Attendance.group_id == group_id,
            Attendance.student_id.in_(student_ids)
        )
        .group_by(Attendance.status)
    )
    result = await db.execute(query)
    
    distribution = AttendanceDistribution()
    for row in result.all():
        status_str = row.status.value.lower() if hasattr(row.status, 'value') else str(row.status).lower()
        if hasattr(distribution, status_str):
            setattr(distribution, status_str, row.count)
    
    return distribution


async def get_student_attendance_history(
    db: AsyncSession,
    student_id: UUID,
    group_id: UUID
) -> List[AttendanceRecord]:
    """Получить историю посещаемости студента."""
    query = (
        select(Attendance)
        .where(
            Attendance.student_id == student_id,
            Attendance.group_id == group_id
        )
        .order_by(Attendance.date.desc())
    )
    result = await db.execute(query)
    records = result.scalars().all()
    
    return [
        AttendanceRecord(
            date=r.date, 
            status=r.status.value.lower() if hasattr(r.status, 'value') else str(r.status).lower(), 
            lesson_topic=None
        )
        for r in records
    ]


async def get_student_attendance_stats(
    db: AsyncSession,
    student_id: UUID,
    group_id: UUID
) -> Dict:
    """Получить статистику посещаемости студента."""
    query = (
        select(Attendance.status, func.count(Attendance.id).label('count'))
        .where(
            Attendance.student_id == student_id,
            Attendance.group_id == group_id
        )
        .group_by(Attendance.status)
    )
    result = await db.execute(query)
    
    stats = {'present': 0, 'late': 0, 'excused': 0, 'absent': 0, 'total': 0}
    for row in result.all():
        status_str = row.status.value.lower() if hasattr(row.status, 'value') else str(row.status).lower()
        stats[status_str] = row.count
        stats['total'] += row.count
    
    if stats['total'] > 0:
        present_equivalent = stats['present'] + stats['late'] * 0.5 + stats['excused'] * 0.5
        stats['rate'] = round(present_equivalent / stats['total'] * 100, 1)
    else:
        stats['rate'] = 0.0
    
    return stats
