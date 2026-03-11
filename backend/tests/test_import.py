import asyncio
import sys
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.schedule_import_service import ScheduleImportService
from app.core.config import settings

async def test():
    # Защита от запуска на production БД
    if settings.ENVIRONMENT not in ("testing", "development"):
        print("❌ ОШИБКА: Этот скрипт можно запускать только в testing/development окружении")
        print(f"   Текущее окружение: {settings.ENVIRONMENT}")
        sys.exit(1)
    
    if "test" not in settings.DATABASE_URL.lower():
        print("⚠️  ПРЕДУПРЕЖДЕНИЕ: DATABASE_URL не содержит 'test'")
        print(f"   URL: {settings.DATABASE_URL}")
        response = input("   Продолжить? (yes/no): ")
        if response.lower() != "yes":
            print("Отменено пользователем")
            sys.exit(0)
    
    # Создаём сессию БД
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        import_service = ScheduleImportService(db)
        
        # Импортируем расписание
        stats = await import_service.import_from_parser(
            teacher_name='Миронов Г.Д.',
            start_date=date(2025, 9, 1),
            end_date=date(2025, 9, 14)
        )
        
        print('Импорт завершён:')
        print(f'  Распарсено: {stats["total_parsed"]}')
        print(f'  Групп создано: {stats["groups_created"]}')
        print(f'  Занятий создано: {stats["lessons_created"]}')
        print(f'  Занятий пропущено: {stats["lessons_skipped"]}')
        print(f'  Группы: {stats["groups"]}')

if __name__ == "__main__":
    asyncio.run(test())
