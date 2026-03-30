import pytest
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models import Group, User, UserRole

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_create_group_and_user():
    """Тест создания группы и студента (Happy Path)"""
    async with AsyncSessionLocal() as session, session.begin():
        # 1. Создаем группу
        new_group = Group(code="TEST-24-1", name="Test Group 1")
        session.add(new_group)
        await session.flush()

        assert new_group.id is not None

        # 2. Создаем пользователя в этой группе
        new_user = User(
            telegram_id=123456789,
            full_name="Ivanov Ivan",
            username="ivan_test",
            role=UserRole.STUDENT,
            group_id=new_group.id,
        )
        session.add(new_user)
        await session.flush()

        # 3. Проверяем, что пользователь сохранился и связан с группой
        result = await session.execute(select(User).where(User.telegram_id == 123456789))
        user_from_db = result.scalar_one()

        assert user_from_db.full_name == "Ivanov Ivan"
        assert user_from_db.group_id == new_group.id

        # Rollback — данные НЕ сохраняются в БД
        await session.rollback()
