"""
Student API endpoints - личный кабинет студента.
Только чтение своих данных.
"""
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_user
from app.models.user import User, UserRole
from app.models.group import Group
from app.models.lab import Lab
from app.models.submission import Submission
from app.models.attendance import Attendance, AttendanceStatus
from app.models.activity import Activity
from app.services.attestation_service import AttestationService

router = APIRouter()


# ============== Profile ==============

@router.get("/profile")
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Профиль студента с информацией о группе."""
    
    group_info = None
    if current_user.group_id:
        group = await db.get(Group, current_user.group_id)
        if group:
            group_info = {
                "id": str(group.id),
                "name": group.name,
                "code": group.code,
            }
    
    return {
        "id": str(current_user.id),
        "full_name": current_user.full_name,
        "username": current_user.username,
        "role": current_user.role.value,
        "group": group_info,
    }


# ============== Attendance ==============

@router.get("/attendance")
async def get_my_attendance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Посещаемость студента со статистикой."""
    
    query = select(Attendance).where(
        Attendance.student_id == current_user.id
    ).order_by(Attendance.date.desc())
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    # Статистика
    total = len(records)
    present = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
    late = sum(1 for r in records if r.status == AttendanceStatus.LATE)
    excused = sum(1 for r in records if r.status == AttendanceStatus.EXCUSED)
    absent = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
    
    rate = round((present + late) / total * 100, 1) if total > 0 else 0.0
    
    return {
        "stats": {
            "total_classes": total,
            "present": present,
            "late": late,
            "excused": excused,
            "absent": absent,
            "attendance_rate": rate,
        },
        "records": [
            {
                "date": r.date.isoformat(),
                "status": r.status.value,
            }
            for r in records
        ],
    }


# ============== Labs ==============

@router.get("/labs")
async def get_my_labs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Лабораторные работы студента со статусами сдачи."""
    
    # Все лабы
    labs_result = await db.execute(
        select(Lab).order_by(Lab.created_at.desc())
    )
    labs = labs_result.scalars().all()
    
    # Сдачи студента
    subs_result = await db.execute(
        select(Submission).where(Submission.user_id == current_user.id)
    )
    submissions = {s.lab_id: s for s in subs_result.scalars().all()}
    
    result = []
    for lab in labs:
        sub = submissions.get(lab.id)
        result.append({
            "id": str(lab.id),
            "title": lab.title,
            "description": lab.description,
            "deadline": lab.deadline.isoformat() if lab.deadline else None,
            "max_grade": lab.max_grade,
            "submission": {
                "status": sub.status.value,
                "grade": sub.grade,
                "feedback": sub.feedback,
                "submitted_at": sub.created_at.isoformat(),
            } if sub else None,
        })
    
    return result


# ============== Attestation ==============

@router.get("/attestation/{attestation_type}")
async def get_my_attestation(
    attestation_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Баллы аттестации студента."""
    
    if attestation_type not in ("first", "second"):
        raise HTTPException(status_code=400, detail="Invalid attestation type")
    
    # Если студент не в группе - нет данных
    if not current_user.group_id:
        return {
            "attestation_type": attestation_type,
            "error": "Студент не привязан к группе",
            "total_score": 0,
            "grade": "-",
            "is_passing": False,
        }
    
    try:
        from app.models.attestation_settings import AttestationType
        att_type = AttestationType.FIRST if attestation_type == "first" else AttestationType.SECOND
        
        service = AttestationService(db)
        result = await service.calculate_student_score(
            student_id=current_user.id,
            group_id=current_user.group_id,
            attestation_type=att_type,
            activity_points=0,
        )
        
        return {
            "attestation_type": attestation_type,
            "total_score": result.total_score,
            "lab_score": result.lab_score,
            "attendance_score": result.attendance_score,
            "activity_score": result.activity_score,
            "grade": result.grade,
            "is_passing": result.is_passing,
            "max_points": result.max_points,
            "min_passing_points": result.min_passing_points,
            "breakdown": {
                "labs": {
                    "raw": result.components_breakdown.labs_raw_score,
                    "weighted": result.components_breakdown.labs_weighted_score,
                    "count": result.components_breakdown.labs_count,
                    "required": result.components_breakdown.labs_required,
                },
                "attendance": {
                    "raw": result.components_breakdown.attendance_raw_score,
                    "weighted": result.components_breakdown.attendance_weighted_score,
                    "total_classes": result.components_breakdown.attendance_total_classes,
                    "present": result.components_breakdown.attendance_present,
                    "late": result.components_breakdown.attendance_late,
                },
                "activity": {
                    "raw": result.components_breakdown.activity_raw_score,
                    "weighted": result.components_breakdown.activity_weighted_score,
                },
            },
        }
    except Exception as e:
        return {
            "attestation_type": attestation_type,
            "error": str(e) or "Настройки аттестации не найдены",
            "total_score": 0,
            "grade": "-",
            "is_passing": False,
        }


# ============== Teacher Contacts ==============

@router.get("/teacher/contacts")
async def get_teacher_contacts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Получить контакты преподавателя группы (только видимые студенту)."""
    
    if not current_user.group_id:
        return {"contacts": None}
    
    # Найти группу и преподавателя
    group = await db.get(Group, current_user.group_id)
    if not group or not group.teacher_id:
        return {"contacts": None}
    
    teacher = await db.get(User, group.teacher_id)
    if not teacher:
        return {"contacts": None}
    
    # Фильтруем контакты по видимости (student или both)
    contacts = teacher.contacts or {}
    visibility = teacher.contact_visibility or {}
    
    filtered = {}
    for field, value in contacts.items():
        vis = visibility.get(field, "none")
        if vis in ("student", "both") and value:
            filtered[field] = value
    
    if not filtered:
        return {"contacts": None}
    
    return {
        "contacts": filtered,
        "teacher_name": teacher.full_name,
    }
