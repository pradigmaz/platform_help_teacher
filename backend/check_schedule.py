"""Проверка расписания в БД."""

import asyncio
from app.db.session import AsyncSessionLocal
from app.models import User, ScheduleItem
from sqlalchemy import select


async def check():
    async with AsyncSessionLocal() as db:
        # Преподаватели с Telegram
        result = await db.execute(select(User).where(User.telegram_id.isnot(None), User.role.in_(["teacher", "admin"])))
        teachers = result.scalars().all()
        print(f"\n=== Преподаватели с Telegram ({len(teachers)}) ===")
        for t in teachers:
            print(f"ID: {t.id}, TG: {t.telegram_id}, ФИО: {t.full_name}, Роль: {t.role}")

        # Расписание
        result = await db.execute(select(ScheduleItem))
        items = result.scalars().all()
        print(f"\n=== Расписание ({len(items)}) ===")
        for item in items:
            print(
                f"ID: {item.id}, Teacher: {item.teacher_id}, "
                f"День: {item.day_of_week.value}, Пара: {item.lesson_number}, "
                f"Предмет: {item.subject}, Active: {item.is_active}"
            )


if __name__ == "__main__":
    asyncio.run(check())
