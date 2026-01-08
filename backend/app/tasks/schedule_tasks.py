"""
Celery tasks для автопарсинга расписания
"""
import logging
import asyncio
from datetime import date, timedelta, datetime
from uuid import UUID

from app.core.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.services.schedule_import_service import ScheduleImportService
from app.services.notification_service import (
    send_to_teacher, format_parse_result, format_parse_error
)
from app.crud.crud_schedule_parser import get_all_enabled_configs
from app.crud.crud_user import get_user_by_id
from app.crud import crud_parse_history

logger = logging.getLogger(__name__)

# Константы
DEFAULT_PARSE_DAYS_AHEAD = 14
RETRY_DELAYS = [60, 300, 900]  # 1min, 5min, 15min (exponential backoff)


@celery_app.task(bind=True, max_retries=3, acks_late=True)
def parse_schedule_task(
    self, 
    teacher_name: str, 
    days_ahead: int = DEFAULT_PARSE_DAYS_AHEAD,
    teacher_id: str = None,
    notify: bool = True,
    config_id: str = None
):
    """Task для парсинга расписания конкретного преподавателя.
    
    acks_late=True — подтверждение после выполнения для graceful shutdown.
    """
    
    async def _parse():
        async with AsyncSessionLocal() as db:
            # Создаём запись истории
            history = None
            if teacher_id:
                history = await crud_parse_history.create_history(
                    db, 
                    UUID(teacher_id),
                    UUID(config_id) if config_id else None
                )
                await db.commit()
            
            try:
                service = ScheduleImportService(db)
                start_date = date.today()
                end_date = start_date + timedelta(days=days_ahead)
                
                logger.info(f"Starting schedule parse for {teacher_name}: {start_date} - {end_date}")
                
                stats = await service.import_from_parser(
                    teacher_name=teacher_name,
                    start_date=start_date,
                    end_date=end_date,
                    smart_update=True
                )
                logger.info(f"Parse complete for {teacher_name}: {stats}")
                
                # Обновляем историю
                if history:
                    await crud_parse_history.complete_history(db, history.id, stats)
                    await db.commit()
                
                # Отправляем уведомление
                if notify and teacher_id:
                    user = await get_user_by_id(db, UUID(teacher_id))
                    if user:
                        message = format_parse_result(stats, stats.get("conflicts_created", 0))
                        await send_to_teacher(user, message)
                
                return stats
                
            except Exception as e:
                # Записываем ошибку в историю
                if history:
                    await crud_parse_history.complete_history(db, history.id, {}, str(e))
                    await db.commit()
                raise
    
    try:
        return asyncio.run(_parse())
    except Exception as e:
        logger.exception(f"Parse failed for {teacher_name}")
        
        # Уведомляем об ошибке после исчерпания retry
        if self.request.retries >= self.max_retries - 1:
            asyncio.run(_notify_error(teacher_id, str(e)))
        
        retry_delay = RETRY_DELAYS[min(self.request.retries, len(RETRY_DELAYS) - 1)]
        raise self.retry(exc=e, countdown=retry_delay)


async def _notify_error(teacher_id: str, error: str):
    """Уведомить об ошибке парсинга"""
    if not teacher_id:
        return
    async with AsyncSessionLocal() as db:
        user = await get_user_by_id(db, UUID(teacher_id))
        if user:
            message = format_parse_error(error)
            await send_to_teacher(user, message)


@celery_app.task
def check_all_schedules():
    """
    Периодическая задача - проверяет все включённые конфиги
    и запускает парсинг если пришло время.
    
    Вызывается каждые 15 минут через Celery Beat.
    """
    
    async def _check():
        async with AsyncSessionLocal() as db:
            configs = await get_all_enabled_configs(db)
            
            now = datetime.now()
            current_day = now.weekday()  # 0=пн, 6=вс
            
            for config in configs:
                if _should_run(config, now, current_day):
                    logger.info(f"Triggering parse for {config.teacher_name}")
                    parse_schedule_task.delay(
                        config.teacher_name, 
                        config.parse_days_ahead,
                        str(config.teacher_id),
                        True,  # notify
                        str(config.id)  # config_id
                    )
                    # Обновляем last_run_at
                    config.last_run_at = now
                    await db.commit()
    
    return asyncio.run(_check())


def _should_run(config, now: datetime, current_day: int) -> bool:
    """Проверить, нужно ли запускать парсинг для конфига"""
    # Проверяем день недели (теперь массив)
    if current_day not in config.days_of_week:
        return False
    
    # Парсим время запуска
    try:
        run_hour, run_minute = map(int, config.run_time.split(":"))
    except (ValueError, AttributeError):
        logger.warning(f"Invalid run_time format for config {config.id}: {config.run_time}")
        return False
    
    # Проверяем что текущее время в пределах 15 минут от запланированного
    current_minutes = now.hour * 60 + now.minute
    run_minutes = run_hour * 60 + run_minute
    
    if abs(current_minutes - run_minutes) > 15:
        return False
    
    # Проверяем что не запускали сегодня
    if config.last_run_at:
        if config.last_run_at.date() == now.date():
            return False
    
    return True
