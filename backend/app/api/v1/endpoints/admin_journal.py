"""
API endpoints для журнала посещаемости и оценок.
"""
import logging
from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_teacher
from app.models import User, Lesson, Attendance, AttendanceStatus, LessonGrade, Group
from app.models.schedule import LessonType
from app.schemas.lesson_grade import (
    LessonGradeCreate, LessonGradeUpdate, LessonGradeResponse, BulkGradeCreate
)
from app.crud import crud_lesson_grade

logger = logging.getLogger(__name__)
router = APIRouter()


# === Lessons with filters ===

@router.get("/lessons")
async def get_journal_lessons(
    group_id: Optional[UUID] = None,
    subject_id: Optional[UUID] = None,
    lesson_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получить занятия для журнала с фильтрами."""
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
    ).order_by(Lesson.date, Lesson.lesson_number)
    
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


# === Attendance ===

@router.get("/attendance")
async def get_journal_attendance(
    group_id: UUID,
    lesson_ids: List[UUID] = Query(default=[]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получить посещаемость для списка занятий."""
    if not lesson_ids:
        return []
    
    result = await db.execute(
        select(Attendance)
        .where(and_(
            Attendance.group_id == group_id,
            Attendance.lesson_id.in_(lesson_ids)
        ))
        .options(selectinload(Attendance.student))
    )
    attendance_list = result.scalars().all()
    
    return [
        {
            "id": str(a.id),
            "lesson_id": str(a.lesson_id) if a.lesson_id else None,
            "student_id": str(a.student_id),
            "student_name": a.student.full_name if a.student else None,
            "status": a.status.value if hasattr(a.status, 'value') else a.status,
            "date": a.date.isoformat(),
            "lesson_number": a.lesson_number,
        }
        for a in attendance_list
    ]


@router.post("/attendance/bulk")
async def bulk_update_attendance(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Массовое обновление посещаемости."""
    lesson_id = UUID(data["lesson_id"])
    records = data["records"]  # [{student_id, status}]
    
    # Получаем занятие
    lesson_result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id)
    )
    lesson = lesson_result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    updated = []
    for record in records:
        student_id = UUID(record["student_id"])
        status = AttendanceStatus(record["status"])
        
        # Ищем существующую запись
        existing_result = await db.execute(
            select(Attendance).where(and_(
                Attendance.lesson_id == lesson_id,
                Attendance.student_id == student_id
            ))
        )
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            existing.status = status
            updated.append(existing)
        else:
            new_attendance = Attendance(
                lesson_id=lesson_id,
                student_id=student_id,
                group_id=lesson.group_id,
                date=lesson.date,
                lesson_number=lesson.lesson_number,
                lesson_type=lesson.lesson_type,
                subgroup=lesson.subgroup,
                status=status,
                created_by=current_user.id
            )
            db.add(new_attendance)
            updated.append(new_attendance)
    
    await db.commit()
    logger.info(f"Bulk updated {len(updated)} attendance records for lesson {lesson_id}")
    
    return {"updated": len(updated)}


# === Grades ===

@router.get("/grades")
async def get_journal_grades(
    lesson_ids: List[UUID] = Query(default=[]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получить оценки для списка занятий."""
    if not lesson_ids:
        return []
    
    result = await db.execute(
        select(LessonGrade)
        .where(LessonGrade.lesson_id.in_(lesson_ids))
        .options(selectinload(LessonGrade.student))
    )
    grades = result.scalars().all()
    
    return [
        {
            "id": str(g.id),
            "lesson_id": str(g.lesson_id),
            "student_id": str(g.student_id),
            "student_name": g.student.full_name if g.student else None,
            "work_number": g.work_number,
            "grade": g.grade,
            "comment": g.comment,
        }
        for g in grades
    ]


@router.post("/grades", response_model=LessonGradeResponse)
async def create_grade(
    data: LessonGradeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Создать оценку."""
    grade = await crud_lesson_grade.upsert_lesson_grade(
        db,
        lesson_id=data.lesson_id,
        student_id=data.student_id,
        grade=data.grade,
        work_number=data.work_number,
        comment=data.comment,
        created_by=current_user.id
    )
    return grade


@router.patch("/grades/{grade_id}", response_model=LessonGradeResponse)
async def update_grade(
    grade_id: UUID,
    data: LessonGradeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Обновить оценку."""
    grade = await crud_lesson_grade.update_lesson_grade(
        db,
        grade_id=grade_id,
        grade=data.grade,
        work_number=data.work_number,
        comment=data.comment
    )
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    return grade


@router.delete("/grades/{grade_id}")
async def delete_grade(
    grade_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Удалить оценку."""
    success = await crud_lesson_grade.delete_lesson_grade(db, grade_id)
    if not success:
        raise HTTPException(status_code=404, detail="Grade not found")
    return {"deleted": True}


@router.post("/grades/bulk")
async def bulk_update_grades(
    data: BulkGradeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Массовое создание/обновление оценок."""
    updated = []
    for grade_data in data.grades:
        grade = await crud_lesson_grade.upsert_lesson_grade(
            db,
            lesson_id=data.lesson_id,
            student_id=UUID(grade_data["student_id"]),
            grade=grade_data["grade"],
            work_number=grade_data.get("work_number"),
            comment=grade_data.get("comment"),
            created_by=current_user.id
        )
        updated.append(grade)
    
    logger.info(f"Bulk updated {len(updated)} grades for lesson {data.lesson_id}")
    return {"updated": len(updated)}


# === Stats ===

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
    # Базовый фильтр занятий
    lesson_filter = [Lesson.group_id == group_id, Lesson.is_cancelled == False]
    if subject_id:
        lesson_filter.append(Lesson.subject_id == subject_id)
    if start_date:
        lesson_filter.append(Lesson.date >= start_date)
    if end_date:
        lesson_filter.append(Lesson.date <= end_date)
    
    # Получаем занятия
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
    
    # Считаем по типам - надёжное сравнение через value
    def get_lesson_type_value(lesson):
        if hasattr(lesson.lesson_type, 'value'):
            return lesson.lesson_type.value.lower()
        return str(lesson.lesson_type).lower()
    
    lectures = sum(1 for l in lessons if get_lesson_type_value(l) == 'lecture')
    labs = sum(1 for l in lessons if get_lesson_type_value(l) == 'lab')
    practices = sum(1 for l in lessons if get_lesson_type_value(l) == 'practice')
    
    # Посещаемость - только для занятий текущей недели
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
    
    # Средняя оценка - только для занятий текущей недели
    grade_result = await db.execute(
        select(func.avg(LessonGrade.grade))
        .where(and_(
            LessonGrade.lesson_id.in_(lesson_ids)
        ))
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
