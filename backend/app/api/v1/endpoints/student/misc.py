"""Student misc endpoints - contacts, semesters."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.audit import ActionType, EntityType, audit_action
from app.models.group import Group
from app.models.user import User

router = APIRouter()


async def _get_group_teacher(db: AsyncSession, group_id: UUID) -> User | None:
    from app.models.teacher_subject import TeacherSubjectAssignment

    result = await db.execute(
        select(User)
        .join(TeacherSubjectAssignment, TeacherSubjectAssignment.teacher_id == User.id)
        .where(
            TeacherSubjectAssignment.group_id == group_id,
            TeacherSubjectAssignment.is_active.is_(True),
        )
        .limit(1)
    )
    return result.scalar_one_or_none()


@router.get("/teacher/contacts")
@audit_action(ActionType.VIEW, EntityType.TEACHER_CONTACTS)
async def get_teacher_contacts(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Получить контакты преподавателя группы."""

    if not current_user.group_id:
        return {"contacts": None}

    group = await db.get(Group, current_user.group_id)
    if not group:
        return {"contacts": None}

    teacher = await _get_group_teacher(db, group.id)
    if not teacher:
        return {"contacts": None}

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


@router.get("/semesters")
@audit_action(ActionType.VIEW, EntityType.SEMESTER)
async def get_available_semesters(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Получить доступные семестры для студента."""
    from app.services.reports.semester_helpers import get_current_semester_from_settings

    if not current_user.group_id:
        return {"semesters": [], "current": None}

    group = await db.get(Group, current_user.group_id)
    hide_previous = True

    if group:
        teacher = await _get_group_teacher(db, group.id)
        if teacher:
            teacher_settings = teacher.teacher_settings or {}
            hide_previous = teacher_settings.get("hide_previous_semester", True)

    # Используем async версию для получения семестра из настроек
    current_year, current_sem = await get_current_semester_from_settings(db)
    current = {"academic_year": current_year, "semester": current_sem}

    semesters = [current]

    if not hide_previous:
        if current_sem == 2:
            semesters.append({"academic_year": current_year, "semester": 1})
        else:
            semesters.append({"academic_year": current_year - 1, "semester": 2})

    return {
        "semesters": semesters,
        "current": current,
        "hide_previous_semester": hide_previous,
    }
