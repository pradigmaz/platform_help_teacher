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
from app.models.submission import Submission, SubmissionStatus
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
        "telegram_id": current_user.telegram_id,
        "vk_id": current_user.vk_id,
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
    """
    Лабораторные работы студента со статусами сдачи.
    Учитывает последовательный доступ (is_sequential).
    """
    
    # Все лабы, отсортированные по номеру
    labs_result = await db.execute(
        select(Lab).order_by(Lab.number.asc(), Lab.created_at.desc())
    )
    labs = labs_result.scalars().all()
    
    # Сдачи студента
    subs_result = await db.execute(
        select(Submission).where(Submission.user_id == current_user.id)
    )
    submissions = {s.lab_id: s for s in subs_result.scalars().all()}
    
    # Определяем номер студента в группе для варианта
    student_position = await _get_student_position(db, current_user)
    
    result = []
    prev_accepted = True  # Первая лаба всегда доступна
    
    for lab in labs:
        sub = submissions.get(lab.id)
        
        # Проверяем доступность
        is_available = prev_accepted or not lab.is_sequential
        
        # Определяем вариант
        variant_number = None
        if lab.variants and student_position:
            variants_count = len(lab.variants)
            variant_number = ((student_position - 1) % variants_count) + 1
        
        result.append({
            "id": str(lab.id),
            "number": lab.number,
            "title": lab.title,
            "topic": lab.topic,
            "description": lab.description,
            "deadline": lab.deadline.isoformat() if lab.deadline else None,
            "max_grade": lab.max_grade,
            "is_available": is_available,
            "variant_number": variant_number,
            "submission": {
                "id": str(sub.id),
                "status": sub.status.value,
                "grade": sub.grade,
                "feedback": sub.feedback,
                "ready_at": sub.ready_at.isoformat() if sub.ready_at else None,
                "accepted_at": sub.accepted_at.isoformat() if sub.accepted_at else None,
            } if sub else None,
        })
        
        # Обновляем флаг для следующей лабы
        if sub and sub.status.value == "ACCEPTED":
            prev_accepted = True
        elif lab.is_sequential:
            prev_accepted = False
    
    return result


@router.get("/labs/{lab_id}")
async def get_lab_detail(
    lab_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Детали лабораторной работы с вариантом студента.
    """
    lab = await db.get(Lab, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    
    # Проверяем доступность (последовательность)
    is_available = await _check_lab_availability(db, current_user.id, lab)
    
    # Определяем вариант студента
    student_position = await _get_student_position(db, current_user)
    variant_number = None
    variant_data = None
    
    if lab.variants and student_position:
        variants_count = len(lab.variants)
        variant_number = ((student_position - 1) % variants_count) + 1
        
        # Находим данные варианта
        for v in lab.variants:
            if v.get("number") == variant_number:
                variant_data = v
                break
    
    # Получаем сдачу студента
    sub_result = await db.execute(
        select(Submission).where(
            Submission.user_id == current_user.id,
            Submission.lab_id == lab_id,
        )
    )
    sub = sub_result.scalar_one_or_none()
    
    return {
        "id": str(lab.id),
        "number": lab.number,
        "title": lab.title,
        "topic": lab.topic,
        "goal": lab.goal,
        "formatting_guide": lab.formatting_guide,
        "theory_content": lab.theory_content,
        "practice_content": lab.practice_content,
        "questions": lab.questions,
        "deadline": lab.deadline.isoformat() if lab.deadline else None,
        "max_grade": lab.max_grade,
        "is_available": is_available,
        "variant_number": variant_number,
        "variant_data": variant_data,
        "submission": {
            "id": str(sub.id),
            "status": sub.status.value,
            "grade": sub.grade,
            "feedback": sub.feedback,
            "ready_at": sub.ready_at.isoformat() if sub.ready_at else None,
            "accepted_at": sub.accepted_at.isoformat() if sub.accepted_at else None,
        } if sub else None,
    }


@router.post("/labs/{lab_id}/ready")
async def mark_lab_ready(
    lab_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Отметить лабу как готовую к сдаче.
    Студент попадает в очередь к преподавателю.
    """
    from datetime import datetime
    
    lab = await db.get(Lab, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    
    # Проверяем доступность
    is_available = await _check_lab_availability(db, current_user.id, lab)
    if not is_available:
        raise HTTPException(status_code=403, detail="Lab is not available yet. Complete previous labs first.")
    
    # Получаем или создаём сдачу
    sub_result = await db.execute(
        select(Submission).where(
            Submission.user_id == current_user.id,
            Submission.lab_id == lab_id,
        )
    )
    sub = sub_result.scalar_one_or_none()
    
    if sub:
        if sub.status.value == "READY":
            raise HTTPException(status_code=400, detail="Already in queue")
        if sub.status.value == "ACCEPTED":
            raise HTTPException(status_code=400, detail="Lab already accepted")
    
    # Определяем вариант
    student_position = await _get_student_position(db, current_user)
    variant_number = None
    if lab.variants and student_position:
        variants_count = len(lab.variants)
        variant_number = ((student_position - 1) % variants_count) + 1
    
    if sub:
        # Обновляем существующую
        sub.status = SubmissionStatus.READY
        sub.ready_at = datetime.utcnow()
        sub.variant_number = variant_number
    else:
        # Создаём новую
        sub = Submission(
            user_id=current_user.id,
            lab_id=lab_id,
            status=SubmissionStatus.READY,
            is_manual=True,
            variant_number=variant_number,
            ready_at=datetime.utcnow(),
        )
        db.add(sub)
    
    await db.commit()
    await db.refresh(sub)
    
    return {
        "status": "ready",
        "submission_id": str(sub.id),
        "variant_number": variant_number,
        "message": "You are now in the queue. Go to the teacher with your notebook.",
    }


@router.post("/labs/{lab_id}/cancel-ready")
async def cancel_lab_ready(
    lab_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Отменить готовность к сдаче (выйти из очереди)."""
    sub_result = await db.execute(
        select(Submission).where(
            Submission.user_id == current_user.id,
            Submission.lab_id == lab_id,
        )
    )
    sub = sub_result.scalar_one_or_none()
    
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    if sub.status.value != "READY":
        raise HTTPException(status_code=400, detail="Not in queue")
    
    sub.status = SubmissionStatus.NEW
    sub.ready_at = None
    
    await db.commit()
    
    return {"status": "cancelled", "message": "Removed from queue"}


# === Helper functions ===

async def _get_student_position(db: AsyncSession, user: User) -> Optional[int]:
    """Получить позицию студента в списке группы (для определения варианта)."""
    if not user.group_id:
        return None
    
    # Получаем всех студентов группы, отсортированных по ФИО
    from app.models import UserRole
    result = await db.execute(
        select(User)
        .where(User.group_id == user.group_id, User.role == UserRole.STUDENT)
        .order_by(User.full_name.asc())
    )
    students = result.scalars().all()
    
    for i, student in enumerate(students):
        if student.id == user.id:
            return i + 1  # 1-based
    
    return None


async def _check_lab_availability(db: AsyncSession, user_id: UUID, lab: Lab) -> bool:
    """Проверить доступность лабы (последовательность)."""
    if lab.number == 1:
        return True
    
    if not lab.is_sequential:
        return True
    
    # Ищем предыдущую лабу того же предмета
    prev_lab_result = await db.execute(
        select(Lab).where(
            Lab.subject_id == lab.subject_id,
            Lab.number == lab.number - 1,
        )
    )
    prev_lab = prev_lab_result.scalar_one_or_none()
    
    if not prev_lab:
        return True  # Нет предыдущей лабы
    
    # Проверяем, сдана ли предыдущая
    prev_sub_result = await db.execute(
        select(Submission).where(
            Submission.user_id == user_id,
            Submission.lab_id == prev_lab.id,
            Submission.status == SubmissionStatus.ACCEPTED,
        )
    )
    prev_sub = prev_sub_result.scalar_one_or_none()
    
    return prev_sub is not None


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


# ============== Semester Settings ==============

@router.get("/semesters")
async def get_available_semesters(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Получить доступные семестры для студента."""
    from datetime import date
    from app.utils.semester import get_current_semester, get_semester_dates, format_semester
    
    if not current_user.group_id:
        return {"semesters": [], "current": None}
    
    # Получить настройки преподавателя
    group = await db.get(Group, current_user.group_id)
    hide_previous = True  # default
    
    if group and group.teacher_id:
        teacher = await db.get(User, group.teacher_id)
        if teacher:
            settings = teacher.teacher_settings or {}
            hide_previous = settings.get("hide_previous_semester", True)
    
    # Текущий семестр
    current_year, current_sem = get_current_semester()
    current = {"academic_year": current_year, "semester": current_sem}
    
    semesters = [current]
    
    # Добавить прошлый семестр если разрешено
    if not hide_previous:
        if current_sem == 2:
            # Прошлый = 1 семестр того же года
            semesters.append({"academic_year": current_year, "semester": 1})
        else:
            # Прошлый = 2 семестр прошлого года
            semesters.append({"academic_year": current_year - 1, "semester": 2})
    
    return {
        "semesters": semesters,
        "current": current,
        "hide_previous_semester": hide_previous,
    }
