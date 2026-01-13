"""Поиск и привязка пользователей."""
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, UserRole
from app.utils.text import normalize_fio, fio_similarity
from .constants import Platform

logger = logging.getLogger(__name__)


def get_social_id_field(platform: Platform):
    """Возвращает поле модели для платформы."""
    return User.telegram_id if platform == "telegram" else User.vk_id


async def find_user_by_social_id(db: AsyncSession, social_id: int, platform: Platform) -> User | None:
    """Поиск пользователя по social_id для конкретной платформы."""
    field = get_social_id_field(platform)
    result = await db.execute(select(User).where(field == social_id))
    return result.scalar_one_or_none()


async def find_student_by_fio(
    db: AsyncSession, 
    group_id: str, 
    input_fio: str
) -> tuple[User | None, list[User]]:
    """
    Поиск студента по ФИО в группе.
    
    Returns:
        (exact_match, similar): точное совпадение и список похожих.
    """
    normalized_input = normalize_fio(input_fio)
    result = await db.execute(
        select(User).where(
            User.group_id == UUID(group_id),
            User.role == UserRole.STUDENT,
            User.telegram_id.is_(None),
            User.vk_id.is_(None)
        )
    )
    students = result.scalars().all()
    
    exact_match = None
    similar = []
    
    for student in students:
        similarity = fio_similarity(normalized_input, student.full_name)
        if similarity == 1.0:
            exact_match = student
            break
        elif similarity >= 0.6:
            similar.append(student)
    
    return exact_match, similar


async def bind_social_id(
    db: AsyncSession,
    user: User, 
    social_id: int, 
    platform: Platform, 
    username: str | None = None
) -> str | None:
    """
    Привязывает social_id к пользователю.
    
    Returns:
        None если успешно, строка с ошибкой если social_id уже занят.
    """
    existing = await find_user_by_social_id(db, social_id, platform)
    if existing and existing.id != user.id:
        platform_name = "Telegram" if platform == "telegram" else "VK"
        logger.warning(
            f"Попытка привязки занятого {platform_name} ID {social_id} "
            f"к пользователю {user.id} ({user.full_name}), "
            f"уже привязан к {existing.id} ({existing.full_name})"
        )
        return f"❌ Этот {platform_name} аккаунт уже привязан к другому пользователю."
    
    if platform == "telegram":
        user.telegram_id = social_id
        if username is not None:
            user.username = username
    else:
        user.vk_id = social_id
    
    return None
