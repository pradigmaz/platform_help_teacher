"""Attendance validators."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from .exceptions import StudentNotFoundError, StudentNotInGroupError


async def validate_student_in_group(
    db: AsyncSession,
    student_id: UUID,
    group_id: UUID
) -> User:
    """
    Проверка принадлежности студента к группе.
    
    Args:
        db: Сессия базы данных
        student_id: ID студента
        group_id: ID группы
        
    Returns:
        User: Объект студента
        
    Raises:
        StudentNotFoundError: Если студент не найден
        StudentNotInGroupError: Если студент не принадлежит группе
    """
    query = select(User).where(User.id == student_id)
    result = await db.execute(query)
    student = result.scalar_one_or_none()
    
    if not student:
        raise StudentNotFoundError(f"Студент с ID {student_id} не найден")
    
    if student.group_id != group_id:
        raise StudentNotInGroupError(
            f"Студент {student_id} не принадлежит группе {group_id}. "
            f"Текущая группа студента: {student.group_id}"
        )
    
    return student
