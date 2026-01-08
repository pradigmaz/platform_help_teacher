"""
Базовые хелперы для сбора данных отчётов.
"""
from typing import Optional, List, Dict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.models.user import User, UserRole
from app.schemas.user import PublicTeacherContacts


async def get_group(db: AsyncSession, group_id: UUID) -> Optional[Group]:
    """Получить группу по ID."""
    query = select(Group).where(Group.id == group_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_user(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """Получить пользователя по ID."""
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_group_students(db: AsyncSession, group_id: UUID) -> List[User]:
    """Получить активных студентов группы."""
    query = (
        select(User)
        .where(
            User.group_id == group_id,
            User.role == UserRole.STUDENT,
            User.is_active == True
        )
        .order_by(User.full_name)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


def get_filtered_teacher_contacts(
    teacher: User,
    target: str  # "student" or "report"
) -> Optional[PublicTeacherContacts]:
    """
    Фильтрация контактов преподавателя по видимости.
    
    target="student" -> visibility in ("student", "both")
    target="report" -> visibility in ("report", "both")
    """
    contacts = teacher.contacts or {}
    visibility = teacher.contact_visibility or {}
    
    if not contacts:
        return None
    
    allowed_visibility = ("student", "both") if target == "student" else ("report", "both")
    
    filtered = {}
    for field, value in contacts.items():
        vis = visibility.get(field, "none")
        if vis in allowed_visibility and value:
            filtered[field] = value
    
    if not filtered:
        return None
    
    return PublicTeacherContacts(
        telegram=filtered.get("telegram"),
        vk=filtered.get("vk"),
        max=filtered.get("max"),
        teacher_name=teacher.full_name,
    )
