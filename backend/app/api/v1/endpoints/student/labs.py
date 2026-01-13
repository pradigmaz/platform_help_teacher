"""Student labs endpoints."""
from typing import Any, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User, UserRole
from app.models.lab import Lab
from app.models.submission import Submission, SubmissionStatus
from app.audit import audit_action, audit_user, ActionType, EntityType
from app.services.lab_visibility import LabVisibilityService
from app.core.limiter import limiter

router = APIRouter()


@router.get("/labs")
@audit_action(ActionType.VIEW, EntityType.LAB)
async def get_my_labs(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Лабораторные работы студента со статусами сдачи.
    
    Лабы фильтруются по расписанию — видны только те, для которых
    уже было занятие с соответствующим work_number.
    """
    if not current_user.group_id:
        return []
    
    visibility_service = LabVisibilityService(db)
    
    # Получаем видимые лабы по предметам {subject_id: [work_numbers]}
    visible_by_subject = await visibility_service.get_visible_lab_numbers_by_subject(
        group_id=current_user.group_id,
        subgroup=current_user.subgroup
    )
    
    # Получаем все опубликованные лабы
    labs_result = await db.execute(
        select(Lab)
        .where(Lab.is_published.is_(True))
        .where(Lab.deleted_at.is_(None))
        .order_by(Lab.number.asc(), Lab.created_at.desc())
    )
    labs = labs_result.scalars().all()
    
    # Фильтруем по видимости с учётом subject_id
    def is_lab_visible(lab: Lab) -> bool:
        # Если у лабы есть subject_id — проверяем по этому предмету
        if lab.subject_id:
            subject_labs = visible_by_subject.get(lab.subject_id, [])
            return lab.number in subject_labs
        # Если subject_id = NULL — проверяем по всем предметам
        for work_numbers in visible_by_subject.values():
            if lab.number in work_numbers:
                return True
        return False
    
    visible_labs = [lab for lab in labs if is_lab_visible(lab)]
    
    # Batch-загрузка информации о дедлайнах (решает N+1)
    labs_deadlines = {
        lab.number: (lab.deadline_5_lessons, lab.deadline_4_lessons)
        for lab in visible_labs
    }
    labs_subjects = {
        lab.number: lab.subject_id
        for lab in visible_labs
    }
    visibility_map = await visibility_service.get_batch_visibility_info(
        lab_numbers=[lab.number for lab in visible_labs],
        group_id=current_user.group_id,
        subgroup=current_user.subgroup,
        labs_deadlines=labs_deadlines,
        labs_subjects=labs_subjects
    )
    
    subs_result = await db.execute(
        select(Submission).where(Submission.user_id == current_user.id)
    )
    submissions = {s.lab_id: s for s in subs_result.scalars().all()}
    
    student_position = await _get_student_position(db, current_user)
    
    result = []
    prev_accepted = True
    
    for lab in visible_labs:
        sub = submissions.get(lab.id)
        is_available = prev_accepted or not lab.is_sequential
        
        variant_number = None
        if lab.variants and student_position:
            variants_count = len(lab.variants)
            variant_number = ((student_position - 1) % variants_count) + 1
        
        # Получаем информацию о дедлайнах из batch-результата
        visibility_info = visibility_map.get(lab.number)
        
        result.append({
            "id": str(lab.id),
            "number": lab.number,
            "title": lab.title,
            "topic": lab.topic,
            "description": lab.description,
            "deadline_5_lessons": lab.deadline_5_lessons,
            "deadline_4_lessons": lab.deadline_4_lessons,
            "max_grade": lab.max_grade,
            "is_available": is_available,
            "variant_number": variant_number,
            "submission": _format_submission(sub) if sub else None,
            # Новые поля дедлайнов
            "visible_from": visibility_info.visible_from.isoformat() if visibility_info and visibility_info.visible_from else None,
            "deadline_active_from": visibility_info.deadline_active_from.isoformat() if visibility_info and visibility_info.deadline_active_from else None,
            "deadline_5_status": visibility_info.deadline_5_status if visibility_info else None,
            "deadline_4_status": visibility_info.deadline_4_status if visibility_info else None,
            "lessons_until_deadline_5": visibility_info.lessons_until_deadline_5 if visibility_info else None,
            "lessons_until_deadline_4": visibility_info.lessons_until_deadline_4 if visibility_info else None,
        })
        
        if sub and sub.status.value == "ACCEPTED":
            prev_accepted = True
        elif lab.is_sequential:
            prev_accepted = False
    
    return result


@router.get("/labs/{lab_id}")
@audit_action(ActionType.VIEW, EntityType.LAB_DETAIL, "lab_id")
async def get_lab_detail(
    lab_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Детали лабораторной работы с вариантом студента."""
    lab = await db.get(Lab, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    
    # Проверяем видимость по расписанию
    if current_user.group_id:
        visibility_service = LabVisibilityService(db)
        visibility_info = await visibility_service.get_visibility_info(
            lab_number=lab.number,
            group_id=current_user.group_id,
            subgroup=current_user.subgroup,
            deadline_5_lessons=lab.deadline_5_lessons,
            deadline_4_lessons=lab.deadline_4_lessons,
            subject_id=lab.subject_id
        )
        
        if not visibility_info.is_visible:
            raise HTTPException(status_code=403, detail="Lab not available yet")
    else:
        visibility_info = None
    
    is_available = await _check_lab_availability(db, current_user.id, lab)
    student_position = await _get_student_position(db, current_user)
    
    variant_number = None
    variant_data = None
    if lab.variants and student_position:
        variants_count = len(lab.variants)
        variant_number = ((student_position - 1) % variants_count) + 1
        for v in lab.variants:
            if v.get("number") == variant_number:
                variant_data = v
                break
    
    sub_result = await db.execute(
        select(Submission).where(
            Submission.user_id == current_user.id,
            Submission.lab_id == lab_id,
        ).order_by(Submission.created_at.desc()).limit(1)
    )
    sub = sub_result.scalar_one_or_none()
    
    response = {
        "id": str(lab.id),
        "number": lab.number,
        "title": lab.title,
        "topic": lab.topic,
        "goal": lab.goal,
        "formatting_guide": lab.formatting_guide,
        "theory_content": lab.theory_content,
        "practice_content": lab.practice_content,
        "questions": lab.questions,
        "deadline_5_lessons": lab.deadline_5_lessons,
        "deadline_4_lessons": lab.deadline_4_lessons,
        "max_grade": lab.max_grade,
        "is_available": is_available,
        "variant_number": variant_number,
        "variant_data": variant_data,
        "submission": _format_submission(sub) if sub else None,
    }
    
    # Добавляем информацию о дедлайнах если есть
    if visibility_info:
        response.update({
            "visible_from": visibility_info.visible_from.isoformat() if visibility_info.visible_from else None,
            "deadline_active_from": visibility_info.deadline_active_from.isoformat() if visibility_info.deadline_active_from else None,
            "deadline_5_status": visibility_info.deadline_5_status,
            "deadline_4_status": visibility_info.deadline_4_status,
            "lessons_until_deadline_5": visibility_info.lessons_until_deadline_5,
            "lessons_until_deadline_4": visibility_info.lessons_until_deadline_4,
        })
    
    return response


@router.post("/labs/{lab_id}/ready")
@limiter.limit("10/hour")
@audit_action(ActionType.SUBMIT, EntityType.SUBMISSION, "lab_id")
async def mark_lab_ready(
    lab_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(audit_user),
) -> dict[str, Any]:
    """Отметить лабу как готовую к сдаче. Rate limit: 10/hour."""
    lab = await db.get(Lab, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    
    # Проверяем видимость по расписанию
    if current_user.group_id:
        visibility_service = LabVisibilityService(db)
        visibility_info = await visibility_service.get_visibility_info(
            lab_number=lab.number,
            group_id=current_user.group_id,
            subgroup=current_user.subgroup,
            deadline_5_lessons=lab.deadline_5_lessons,
            deadline_4_lessons=lab.deadline_4_lessons,
            subject_id=lab.subject_id
        )
        
        if not visibility_info.is_visible:
            raise HTTPException(status_code=403, detail="Lab not available yet by schedule")
    
    is_available = await _check_lab_availability(db, current_user.id, lab)
    if not is_available:
        raise HTTPException(status_code=403, detail="Lab is not available yet")
    
    sub_result = await db.execute(
        select(Submission).where(
            Submission.user_id == current_user.id,
            Submission.lab_id == lab_id,
        ).order_by(Submission.created_at.desc()).limit(1)
    )
    sub = sub_result.scalar_one_or_none()
    
    if sub:
        if sub.status.value == "READY":
            raise HTTPException(status_code=400, detail="Already in queue")
        if sub.status.value == "ACCEPTED":
            raise HTTPException(status_code=400, detail="Lab already accepted")
    
    student_position = await _get_student_position(db, current_user)
    variant_number = None
    if lab.variants and student_position:
        variants_count = len(lab.variants)
        variant_number = ((student_position - 1) % variants_count) + 1
    
    if sub:
        sub.status = SubmissionStatus.READY
        sub.ready_at = datetime.utcnow()
        sub.variant_number = variant_number
    else:
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
        "message": "You are now in the queue.",
    }


@router.post("/labs/{lab_id}/cancel-ready")
@audit_action(ActionType.CANCEL, EntityType.SUBMISSION, "lab_id")
async def cancel_lab_ready(
    lab_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(audit_user),
) -> dict[str, Any]:
    """Отменить готовность к сдаче."""
    sub_result = await db.execute(
        select(Submission).where(
            Submission.user_id == current_user.id,
            Submission.lab_id == lab_id,
        ).order_by(Submission.created_at.desc()).limit(1)
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


# === Helpers ===

def _format_submission(sub: Submission) -> dict:
    return {
        "id": str(sub.id),
        "status": sub.status.value,
        "grade": sub.grade,
        "feedback": sub.feedback,
        "ready_at": sub.ready_at.isoformat() if sub.ready_at else None,
        "accepted_at": sub.accepted_at.isoformat() if sub.accepted_at else None,
    }


async def _get_student_position(db: AsyncSession, user: User) -> Optional[int]:
    """Получить позицию студента в списке группы."""
    if not user.group_id:
        return None
    
    result = await db.execute(
        select(User)
        .where(User.group_id == user.group_id, User.role == UserRole.STUDENT)
        .order_by(User.full_name.asc())
    )
    students = result.scalars().all()
    
    for i, student in enumerate(students):
        if student.id == user.id:
            return i + 1
    return None


async def _check_lab_availability(db: AsyncSession, user_id: UUID, lab: Lab) -> bool:
    """Проверить доступность лабы."""
    if lab.number == 1 or not lab.is_sequential:
        return True
    
    prev_lab_result = await db.execute(
        select(Lab).where(
            Lab.subject_id == lab.subject_id,
            Lab.number == lab.number - 1,
        )
    )
    prev_lab = prev_lab_result.scalar_one_or_none()
    
    if not prev_lab:
        return True
    
    prev_sub_result = await db.execute(
        select(Submission).where(
            Submission.user_id == user_id,
            Submission.lab_id == prev_lab.id,
            Submission.status == SubmissionStatus.ACCEPTED,
        )
    )
    return prev_sub_result.scalar_one_or_none() is not None
