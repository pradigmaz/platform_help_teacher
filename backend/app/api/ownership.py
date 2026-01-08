"""
Ownership verification для защиты от IDOR атак.
Проверяет, что пользователь имеет право доступа к ресурсу.
"""
import logging
from typing import Optional, Callable, Any
from uuid import UUID
from functools import wraps

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


class OwnershipError(HTTPException):
    """Ошибка доступа к чужому ресурсу."""
    def __init__(self, resource_type: str = "resource"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You don't have permission to access this {resource_type}"
        )


def check_ownership(
    resource: Any,
    user: User,
    owner_field: str = "created_by_id",
    resource_type: str = "resource",
    allow_admin: bool = True
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
        logger.warning(
            f"Resource {resource_type} has no {owner_field}, skipping ownership check"
        )
        return True
    
    # Сравниваем с текущим пользователем
    if owner_id != user.id:
        logger.warning(
            f"IDOR attempt: user={user.id} tried to access {resource_type} "
            f"owned by {owner_id}"
        )
        raise OwnershipError(resource_type)
    
    return True


def check_student_access(
    student_id: UUID,
    user: User,
    allow_teacher: bool = True,
    allow_admin: bool = True
) -> bool:
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
    
    logger.warning(
        f"IDOR attempt: user={user.id} (role={user.role}) "
        f"tried to access student={student_id} data"
    )
    raise OwnershipError("student data")


def check_group_access(
    group_id: UUID,
    user: User,
    db: AsyncSession = None
) -> bool:
    """
    Проверяет доступ к группе.
    
    Студент может видеть только свою группу.
    Преподаватель — группы своих предметов.
    Админ — все группы.
    
    Args:
        group_id: ID группы
        user: Текущий пользователь
        db: Сессия БД (для проверки связи преподаватель-группа)
    
    Returns:
        True если доступ разрешён
    """
    # Админы
    if user.role == UserRole.ADMIN:
        return True
    
    # Преподаватели имеют доступ ко всем группам (упрощённо)
    # TODO: Добавить проверку teacher_subject -> subject_group
    if user.role == UserRole.TEACHER:
        return True
    
    # Студент — только своя группа
    if user.group_id == group_id:
        return True
    
    logger.warning(
        f"IDOR attempt: user={user.id} (group={user.group_id}) "
        f"tried to access group={group_id}"
    )
    raise OwnershipError("group")
