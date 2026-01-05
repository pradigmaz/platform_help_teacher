"""
Celery tasks для автопарсинга расписания
"""
import logging
import asyncio
from datetime import date, timedelta, datetime
from app.core.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.services.schedule_import_service import ScheduleImportService
from app.crud.crud_schedule_parser import get_all_enabled_configs

logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper to run async code in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def parse_schedule_task(self, teacher_name: str, days_ahead: int = 14):
    """
    Task для парсинга расписания конкретного преподавателя
    """
    async def _parse():
        async with AsyncSessionLocal() as db:
            service = ScheduleImportService(db)
            start_date = date.today()
            end_date = start_date + timedelta(days=days_ahead)
            
            logger.info(f"Starting schedule parse for {teacher_name}: {start_date} - {end_date}")
            
            try:
                stats = await service.import_from_parser(
                    teacher_name=teacher_name,
                    start_date=start_date,
                    end_date=end_date,
                    smart_update=True
                )
                logger.info(f"Parse complete for {teacher_name}: {stats}")
                return stats
            except Exception as e:
                logger.exception(f"Parse failed for {teacher_name}")
                raise self.retry(exc=e, countdown=60)
    
    return run_async(_parse())


@celery_app.task
def check_all_schedules():
    """
    Периодическая задача - проверяет все включённые конфиги
    и запускает парсинг если пришло время
    """
    async def _check():
        async with AsyncSessionLocal() as db:
            configs = await get_all_enabled_configs(db)
            
            now = datetime.now()
            current_day = now.weekday()  # 0=пн, 6=вс
            current_time = now.strftime("%H:%M")
            
            for config in configs:
                # Проверяем день и время (с погрешностью в час)
                if config.day_of_week == current_day:
                    config_hour = int(config.run_time.split(":")[0])
                    current_hour = now.hour
                    
                    if abs(config_hour - current_hour) <= 1:
                        logger.info(f"Triggering parse for {config.teacher_name}")
                        parse_schedule_task.delay(
                            config.teacher_name, 
                            config.parse_days_ahead
                        )
    
    return run_async(_check())
