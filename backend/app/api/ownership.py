"""
Ownership verification для защиты от IDOR атак.
Проверяет, что пользователь имеет право доступа к ресурсу.
"""

import logging
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


class OwnershipError(HTTPException):
    """Ошибка доступа к чужому ресурсу."""

    def __init__(self, resource_type: str = "resource"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"You don't have permission to access this {resource_type}"
        )


def check_ownership(
    resource: Any,
    user: User,
    owner_field: str = "created_by_id",
    resource_type: str = "resource",
    allow_admin: bool = True,
) -> bool:
    """
    Проверяет ownership ресурса.

    Args:
        resource: Объект ресурса (модель SQLAlchemy)
        user: Текущий пользователь
        owner_field: Имя поля с ID владельца
        resource_type: Тип ресурса для сообщения об ошибке
        allow_admin: Разрешить доступ админам

    Returns:
        True если доступ разрешён

    Raises:
        OwnershipError: Если доступ запрещён
    """
    # Админы имеют доступ ко всему
    if allow_admin and user.role == UserRole.ADMIN:
        return True

    # Получаем ID владельца
    owner_id = getattr(resource, owner_field, None)

    # Если поля нет — пропускаем проверку (legacy данные)
    if owner_id is None:
        logger.warning(f"Resource {resource_type} has no {owner_field}, skipping ownership check")
        return True

    # Сравниваем с текущим пользователем
    if owner_id != user.id:
        logger.warning(f"IDOR attempt: user={user.id} tried to access {resource_type} owned by {owner_id}")
        raise OwnershipError(resource_type)

    return True


def check_student_access(student_id: UUID, user: User, allow_teacher: bool = True, allow_admin: bool = True) -> bool:
    """
    Проверяет доступ к данным студента.

    Студент может видеть только свои данные.
    Преподаватель и админ — всех.

    Args:
        student_id: ID студента, к данным которого запрашивается доступ
        user: Текущий пользователь
        allow_teacher: Разрешить доступ преподавателям
        allow_admin: Разрешить доступ админам

    Returns:
        True если доступ разрешён

    Raises:
        OwnershipError: Если доступ запрещён
    """
    # Админы
    if allow_admin and user.role == UserRole.ADMIN:
        return True

    # Преподаватели
    if allow_teacher and user.role == UserRole.TEACHER:
        return True

    # Студент может видеть только себя
    if user.id == student_id:
        return True

    logger.warning(f"IDOR attempt: user={user.id} (role={user.role}) tried to access student={student_id} data")
    raise OwnershipError("student data")


async def check_group_access(group_id: UUID, user: User, db: AsyncSession = None) -> bool:
    """
    Проверяет доступ к группе.

    Студент может видеть только свою группу.
    Преподаватель — группы своих предметов через teacher_subject_assignments.
    Админ — все группы.

    Args:
        group_id: ID группы
        user: Текущий пользователь
        db: Сессия БД (для проверки связи преподаватель-группа)

    Returns:
        True если доступ разрешён

    Raises:
        OwnershipError: Если доступ запрещён
    """
    # Админы
    if user.role == UserRole.ADMIN:
        return True

    # Преподаватели — проверяем через teacher_subject_assignments
    if user.role == UserRole.TEACHER:
        if db is None:
            logger.error("check_group_access called without db session for teacher")
            raise OwnershipError("group")

        from sqlalchemy import or_, select

        from app.models.teacher_subject import TeacherSubjectAssignment

        result = await db.execute(
            select(TeacherSubjectAssignment.id)
            .where(
                TeacherSubjectAssignment.teacher_id == user.id,
                or_(
                    TeacherSubjectAssignment.group_id == group_id,
                    TeacherSubjectAssignment.group_id.is_(None),  # лекционный поток
                ),
                TeacherSubjectAssignment.is_active.is_(True),
            )
            .limit(1)
        )
        if result.scalar_one_or_none() is not None:
            return True

        # Нет доступа — логируем IDOR попытку
        logger.warning(f"IDOR attempt: teacher={user.id} tried to access group={group_id}")
        raise OwnershipError("group")

    # Студент — только своя группа
    if user.group_id == group_id:
        return True

    logger.warning(f"IDOR attempt: user={user.id} (group={user.group_id}) tried to access group={group_id}")
    raise OwnershipError("group")
