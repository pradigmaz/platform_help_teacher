from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, UserRole

async def get_by_social_id(db: AsyncSession, social_id: int) -> Optional[User]:
    """
    Получение пользователя по telegram_id (social_id)
    """
    result = await db.execute(select(User).where(User.social_id == social_id))
    return result.scalar_one_or_none()

async def upsert_user(
    db: AsyncSession, 
    social_id: int, 
    full_name: str, 
    username: Optional[str], 
    group_id: UUID,
    role: UserRole = UserRole.STUDENT
) -> User:
    """
    Создание или обновление пользователя (upsert).
    ВНИМАНИЕ: Не делает commit! Это должен делать вызывающий код.
    """
    user = await get_by_social_id(db, social_id)
    
    if user:
        # Обновляем существующего пользователя
        user.full_name = full_name
        user.username = username
        user.group_id = group_id
        user.role = role
    else:
        # Создаем нового пользователя
        user = User(
            social_id=social_id,
            full_name=full_name,
            username=username,
            group_id=group_id,
            role=role,
            is_active=True
        )
        db.add(user)
    
    # FIX: Удален db.commit(). Обеспечиваем атомарность на уровне сервиса/роутера.
    # Если нужен ID сразу, можно использовать await db.flush(), но лучше комитить в конце.
    return user