"""
Celery tasks для автопарсинга расписания.

ВАЖНО: Используем синхронные сессии (SyncSessionLocal) для совместимости
с Celery prefork worker. asyncio.run() в prefork вызывает "Event loop is closed".
"""
import logging
from datetime import date, timedelta, datetime
from uuid import UUID
from typing import Optional

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.db.session import SyncSessionLocal
from app.services.schedule_constants import MSK_TZ, today_msk
from app.models.schedule_parser_config import ScheduleParserConfig
from app.models.parse_history import ParseHistory
from app.models.user import User

logger = logging.getLogger(__name__)

# Константы
DEFAULT_PARSE_DAYS_AHEAD = 14
RETRY_DELAYS = [60, 300, 900]  # 1min, 5min, 15min


def _get_all_enabled_configs_sync(db) -> list[ScheduleParserConfig]:
    """Синхронная версия get_all_enabled_configs для Celery"""
    result = db.execute(
        select(ScheduleParserConfig).where(ScheduleParserConfig.enabled == True)
    )
    return list(result.scalars().all())


def _get_user_by_id_sync(db, user_id: UUID) -> Optional[User]:
    """Синхронная версия get_user_by_id для Celery"""
    result = db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


def _create_history_sync(db, teacher_id: UUID, config_id: Optional[UUID] = None) -> ParseHistory:
    """Синхронная версия create_history для Celery"""
    history = ParseHistory(
        teacher_id=teacher_id,
        config_id=config_id,
        status="running"
    )
    db.add(history)
    db.flush()
    return history


def _complete_history_sync(db, history_id: UUID, stats: dict, error: Optional[str] = None):
    """Синхронная версия complete_history для Celery"""
    result = db.execute(select(ParseHistory).where(ParseHistory.id == history_id))
    history = result.scalar_one_or_none()
    if not history:
        return
    
    history.finished_at = datetime.utcnow()
    history.status = "failed" if error else "success"
    history.lessons_created = stats.get("lessons_created", 0)
    history.lessons_skipped = stats.get("lessons_skipped", 0)
    history.conflicts_created = stats.get("conflicts_created", 0)
    history.error_message = error


def _send_notification_sync(user: User, message: str):
    """Синхронная отправка уведомлений (через requests)"""
    import os
    import requests
    
    if user.telegram_id:
        try:
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            if bot_token:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                requests.post(url, json={
                    "chat_id": user.telegram_id,
                    "text": message
                }, timeout=10)
                logger.info(f"Telegram notification sent to {user.telegram_id}")
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
    
    if user.vk_id:
        try:
            from app.bots.vk_bot import send_message_sync
            send_message_sync(user.vk_id, message)
            logger.info(f"VK notification sent to {user.vk_id}")
        except Exception as e:
            logger.error(f"Failed to send VK notification: {e}")


def _format_parse_result(stats: dict, conflicts_count: int) -> str:
    """Форматировать результат парсинга"""
    lines = ["📅 Автопарсинг расписания завершён\n"]
    
    if stats.get("lessons_created", 0) > 0:
        lines.append(f"✅ Создано занятий: {stats['lessons_created']}")
    
    if stats.get("lessons_skipped", 0) > 0:
        lines.append(f"⏭ Без изменений: {stats['lessons_skipped']}")
    
    if conflicts_count > 0:
        lines.append(f"\n⚠️ Обнаружено конфликтов: {conflicts_count}")
        lines.append("Проверьте в разделе Расписание")
    
    return "\n".join(lines)


def _format_parse_error(error: str) -> str:
    """Форматировать ошибку парсинга"""
    return f"❌ Ошибка автопарсинга расписания\n\n{error[:200]}"


@celery_app.task(bind=True, max_retries=3, acks_late=True)
def parse_schedule_task(
    self, 
    teacher_name: str, 
    days_ahead: int = DEFAULT_PARSE_DAYS_AHEAD,
    teacher_id: str = None,
    notify: bool = True,
    config_id: str = None
):
    """
    Task для парсинга расписания конкретного преподавателя.
    
    Использует синхронную сессию для совместимости с Celery prefork.
    Парсинг выполняется через HTTP запросы (синхронно).
    """
    try:
        with SyncSessionLocal() as db:
            history = None
            if teacher_id:
                history = _create_history_sync(db, UUID(teacher_id), UUID(config_id) if config_id else None)
                db.commit()
            
            try:
                from app.services.schedule_parser import get_parser_sync
                
                parser = get_parser_sync()
                start_date = today_msk()
                end_date = start_date + timedelta(days=days_ahead)
                
                logger.info(f"Starting schedule parse for {teacher_name}: {start_date} - {end_date}")
                
                stats = parser.parse_and_import_sync(
                    db=db,
                    teacher_name=teacher_name,
                    start_date=start_date,
                    end_date=end_date
                )
                
                logger.info(f"Parse complete for {teacher_name}: {stats}")
                
                if history:
                    _complete_history_sync(db, history.id, stats)
                    db.commit()
                
                if notify and teacher_id:
                    user = _get_user_by_id_sync(db, UUID(teacher_id))
                    if user:
                        message = _format_parse_result(stats, stats.get("conflicts_created", 0))
                        _send_notification_sync(user, message)
                
                return stats
                
            except Exception as e:
                if history:
                    _complete_history_sync(db, history.id, {}, str(e))
                    db.commit()
                raise
    
    except Exception as e:
        logger.exception(f"Parse failed for {teacher_name}")
        
        # Уведомляем об ошибке после исчерпания retry
        if self.request.retries >= self.max_retries - 1:
            if teacher_id:
                with SyncSessionLocal() as db:
                    user = _get_user_by_id_sync(db, UUID(teacher_id))
                    if user:
                        _send_notification_sync(user, _format_parse_error(str(e)))
        
        retry_delay = RETRY_DELAYS[min(self.request.retries, len(RETRY_DELAYS) - 1)]
        raise self.retry(exc=e, countdown=retry_delay)


@celery_app.task
def check_all_schedules():
    """
    Периодическая задача - проверяет все включённые конфиги
    и запускает парсинг если пришло время.
    
    Вызывается каждые 15 минут через Celery Beat.
    Использует синхронную сессию для совместимости с prefork worker.
    """
    with SyncSessionLocal() as db:
        configs = _get_all_enabled_configs_sync(db)
        
        now = datetime.now(MSK_TZ)
        current_day = now.weekday()
        
        for config in configs:
            if _should_run(config, now, current_day):
                logger.info(f"Triggering parse for {config.teacher_name}")
                parse_schedule_task.delay(
                    config.teacher_name, 
                    config.parse_days_ahead,
                    str(config.teacher_id),
                    True,
                    str(config.id)
                )
                # Обновляем last_run_at
                config.last_run_at = now
                db.commit()
    
    return {"checked": len(configs) if 'configs' in dir() else 0}


def _should_run(config, now: datetime, current_day: int) -> bool:
    """Проверить, нужно ли запускать парсинг для конфига"""
    if current_day not in config.days_of_week:
        return False
    
    try:
        run_hour, run_minute = map(int, config.run_time.split(":"))
    except (ValueError, AttributeError):
        logger.warning(f"Invalid run_time format for config {config.id}: {config.run_time}")
        return False
    
    current_minutes = now.hour * 60 + now.minute
    run_minutes = run_hour * 60 + run_minute
    
    if abs(current_minutes - run_minutes) > 15:
        return False
    
    if config.last_run_at:
        if config.last_run_at.date() == now.date():
            return False
    
    return True
