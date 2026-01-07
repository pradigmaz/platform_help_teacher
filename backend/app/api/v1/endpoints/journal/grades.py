"""
API endpoints для оценок и посещаемости журнала.
"""
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_teacher
from app.models import User, Lesson, Attendance, AttendanceStatus, LessonGrade
from app.schemas.lesson_grade import (
    LessonGradeCreate, LessonGradeUpdate, LessonGradeResponse, 
    BulkGradeCreate, BulkAttendanceUpdate, GradeItem
)
from app.crud import crud_lesson_grade
from app.core.limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter()


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
@limiter.limit("30/minute")
async def bulk_update_attendance(
    request: Request,
    data: BulkAttendanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Массовое обновление посещаемости."""
    lesson_result = await db.execute(
        select(Lesson)
        .where(Lesson.id == data.lesson_id)
        .options(selectinload(Lesson.group))
    )
    lesson = lesson_result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Проверка принадлежности студентов к группе (#5)
    group_result = await db.execute(
        select(User.id).where(User.group_id == lesson.group_id)
    )
    group_student_ids = {row[0] for row in group_result.fetchall()}
    
    for record in data.records:
        if record.student_id not in group_student_ids:
            raise HTTPException(
                status_code=400, 
                detail=f"Student {record.student_id} not in group {lesson.group_id}"
            )
    
    updated = []
    for record in data.records:
        status = AttendanceStatus(record.status)
        
        existing_result = await db.execute(
            select(Attendance).where(and_(
                Attendance.lesson_id == data.lesson_id,
                Attendance.student_id == record.student_id
            ))
        )
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            existing.status = status
            updated.append(existing)
        else:
            new_attendance = Attendance(
                lesson_id=data.lesson_id,
                student_id=record.student_id,
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
    logger.info(f"Bulk updated {len(updated)} attendance records for lesson {data.lesson_id}")
    
    return {"updated": len(updated)}


@router.delete("/attendance")
async def delete_attendance(
    lesson_id: UUID = Query(...),
    student_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Удалить запись посещаемости по lesson_id и student_id."""
    result = await db.execute(
        select(Attendance).where(and_(
            Attendance.lesson_id == lesson_id,
            Attendance.student_id == student_id
        ))
    )
    attendance = result.scalar_one_or_none()
    if not attendance:
        return {"deleted": False, "message": "Attendance not found"}
    
    await db.delete(attendance)
    await db.commit()
    logger.info(f"Deleted attendance for lesson {lesson_id}, student {student_id}")
    return {"deleted": True}


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


@router.delete("/grades")
async def delete_grade_by_lesson_student(
    lesson_id: UUID = Query(...),
    student_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Удалить оценку по lesson_id и student_id."""
    result = await db.execute(
        select(LessonGrade).where(and_(
            LessonGrade.lesson_id == lesson_id,
            LessonGrade.student_id == student_id
        ))
    )
    grade = result.scalar_one_or_none()
    if not grade:
        return {"deleted": False, "message": "Grade not found"}
    
    await db.delete(grade)
    await db.commit()
    logger.info(f"Deleted grade for lesson {lesson_id}, student {student_id}")
    return {"deleted": True}


@router.post("/grades/bulk")
@limiter.limit("30/minute")
async def bulk_update_grades(
    request: Request,
    data: BulkGradeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Массовое создание/обновление оценок."""
    updated = []
    for grade_item in data.grades:
        grade = await crud_lesson_grade.upsert_lesson_grade(
            db,
            lesson_id=data.lesson_id,
            student_id=grade_item.student_id,
            grade=grade_item.grade,
            work_number=grade_item.work_number,
            comment=grade_item.comment,
            created_by=current_user.id
        )
        updated.append(grade)
    
    logger.info(f"Bulk updated {len(updated)} grades for lesson {data.lesson_id}")
    return {"updated": len(updated)}
