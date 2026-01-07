"""
API endpoints для занятий журнала.
"""
import logging
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_teacher
from app.models import User, Lesson, Attendance, AttendanceStatus, LessonGrade, Group

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/lessons")
async def get_journal_lessons(
    group_id: Optional[UUID] = None,
    subject_id: Optional[UUID] = None,
    lesson_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0, description="Пропустить записей"),
    limit: int = Query(100, ge=1, le=500, description="Лимит записей"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получить занятия для журнала с фильтрами и пагинацией."""
    query = select(Lesson)
    
    if group_id:
        query = query.where(Lesson.group_id == group_id)
    if subject_id:
        query = query.where(Lesson.subject_id == subject_id)
    if lesson_type:
        query = query.where(Lesson.lesson_type == lesson_type)
    if start_date:
        query = query.where(Lesson.date >= start_date)
    if end_date:
        query = query.where(Lesson.date <= end_date)
    
    query = query.options(
        selectinload(Lesson.subject),
        selectinload(Lesson.grades),
        selectinload(Lesson.group)
    ).order_by(Lesson.date, Lesson.lesson_number).offset(skip).limit(limit)
    
    result = await db.execute(query)
    lessons = result.scalars().all()
    
    return [
        {
            "id": str(l.id),
            "date": l.date.isoformat(),
            "lesson_number": l.lesson_number,
            "lesson_type": l.lesson_type.value if hasattr(l.lesson_type, 'value') else l.lesson_type,
            "topic": l.topic,
            "work_number": l.work_number,
            "lecture_work_type": l.lecture_work_type,
            "subgroup": l.subgroup,
            "is_cancelled": l.is_cancelled,
            "subject_id": str(l.subject_id) if l.subject_id else None,
            "subject_name": l.subject.name if l.subject else None,
            "group_id": str(l.group_id),
            "group_name": l.group.name if l.group else None,
        }
        for l in lessons
    ]


def _get_lesson_type_value(lesson):
    """Надёжное сравнение типа занятия через value."""
    if hasattr(lesson.lesson_type, 'value'):
        return lesson.lesson_type.value.lower()
    return str(lesson.lesson_type).lower()


@router.get("/stats")
async def get_journal_stats(
    group_id: UUID,
    subject_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получить статистику журнала для группы."""
    lesson_filter = [Lesson.group_id == group_id, Lesson.is_cancelled == False]
    if subject_id:
        lesson_filter.append(Lesson.subject_id == subject_id)
    if start_date:
        lesson_filter.append(Lesson.date >= start_date)
    if end_date:
        lesson_filter.append(Lesson.date <= end_date)
    
    lessons_result = await db.execute(
        select(Lesson).where(and_(*lesson_filter))
    )
    lessons = lessons_result.scalars().all()
    lesson_ids = [l.id for l in lessons]
    
    if not lesson_ids:
        return {
            "total_lessons": 0,
            "lectures": 0,
            "labs": 0,
            "practices": 0,
            "attendance_rate": 0,
            "average_grade": 0,
            "by_status": {},
        }
    
    lectures = sum(1 for l in lessons if _get_lesson_type_value(l) == 'lecture')
    labs = sum(1 for l in lessons if _get_lesson_type_value(l) == 'lab')
    practices = sum(1 for l in lessons if _get_lesson_type_value(l) == 'practice')
    
    attendance_result = await db.execute(
        select(Attendance.status, func.count(Attendance.id))
        .where(and_(
            Attendance.lesson_id.in_(lesson_ids),
            Attendance.group_id == group_id
        ))
        .group_by(Attendance.status)
    )
    attendance_stats = dict(attendance_result.all())
    
    total_attendance = sum(attendance_stats.values())
    present_count = attendance_stats.get(AttendanceStatus.PRESENT, 0) + attendance_stats.get(AttendanceStatus.LATE, 0)
    attendance_rate = round(present_count / total_attendance * 100, 1) if total_attendance > 0 else None
    
    grade_result = await db.execute(
        select(func.avg(LessonGrade.grade))
        .where(and_(LessonGrade.lesson_id.in_(lesson_ids)))
    )
    avg_grade = grade_result.scalar()
    average_grade = round(float(avg_grade), 2) if avg_grade else None
    
    return {
        "total_lessons": len(lessons),
        "lectures": lectures,
        "labs": labs,
        "practices": practices,
        "attendance_rate": attendance_rate,
        "average_grade": average_grade,
        "by_status": {
            "present": attendance_stats.get(AttendanceStatus.PRESENT, 0),
            "late": attendance_stats.get(AttendanceStatus.LATE, 0),
            "excused": attendance_stats.get(AttendanceStatus.EXCUSED, 0),
            "absent": attendance_stats.get(AttendanceStatus.ABSENT, 0),
        },
    }
