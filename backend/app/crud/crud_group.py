from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Group

async def get_by_code(db: AsyncSession, code: str) -> Optional[Group]:
    """
    Получение группы по инвайт-коду
    """
    result = await db.execute(select(Group).where(Group.code == code))
    return result.scalar_one_or_none()
