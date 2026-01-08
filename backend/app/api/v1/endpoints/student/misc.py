"""Student misc endpoints - contacts, semesters."""
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.group import Group

router = APIRouter()


@router.get("/teacher/contacts")
async def get_teacher_contacts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Получить контакты преподавателя группы."""
    
    if not current_user.group_id:
        return {"contacts": None}
    
    group = await db.get(Group, current_user.group_id)
    if not group or not group.teacher_id:
        return {"contacts": None}
    
    teacher = await db.get(User, group.teacher_id)
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
async def get_available_semesters(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Получить доступные семестры для студента."""
    from app.utils.semester import get_current_semester
    
    if not current_user.group_id:
        return {"semesters": [], "current": None}
    
    group = await db.get(Group, current_user.group_id)
    hide_previous = True
    
    if group and group.teacher_id:
        teacher = await db.get(User, group.teacher_id)
        if teacher:
            settings = teacher.teacher_settings or {}
            hide_previous = settings.get("hide_previous_semester", True)
    
    current_year, current_sem = get_current_semester()
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
