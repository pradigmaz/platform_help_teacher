"""
Сервис уведомлений через Telegram/VK
"""
import logging
from typing import Optional

from app.models.user import User

logger = logging.getLogger(__name__)


async def send_to_teacher(user: User, message: str) -> dict:
    """
    Отправить уведомление преподавателю через подключённые каналы.
    Returns: {"telegram": bool, "vk": bool}
    """
    result = {"telegram": False, "vk": False}
    
    if user.telegram_id:
        result["telegram"] = await _send_telegram(user.telegram_id, message)
    
    if user.vk_id:
        result["vk"] = await _send_vk(user.vk_id, message)
    
    return result


async def _send_telegram(chat_id: int, message: str) -> bool:
    """Отправить сообщение в Telegram"""
    try:
        from app.bots.telegram_bot import bot
        await bot.send_message(chat_id=chat_id, text=message)
        logger.info(f"Telegram notification sent to {chat_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")
        return False


async def _send_vk(user_id: int, message: str) -> bool:
    """Отправить сообщение в VK"""
    try:
        from app.bots.vk_bot import send_message_sync
        success = send_message_sync(user_id, message)
        if success:
            logger.info(f"VK notification sent to {user_id}")
        return success
    except Exception as e:
        logger.error(f"Failed to send VK notification: {e}")
        return False


def format_parse_result(stats: dict, conflicts_count: int) -> str:
    """Форматировать результат парсинга для уведомления"""
    lines = ["📅 Автопарсинг расписания завершён\n"]
    
    if stats.get("lessons_created", 0) > 0:
        lines.append(f"✅ Создано занятий: {stats['lessons_created']}")
    
    if stats.get("lessons_skipped", 0) > 0:
        lines.append(f"⏭ Без изменений: {stats['lessons_skipped']}")
    
    if conflicts_count > 0:
        lines.append(f"\n⚠️ Обнаружено конфликтов: {conflicts_count}")
        lines.append("Проверьте в разделе Расписание")
    
    if stats.get("semester_end_detected"):
        lines.append(f"\n📌 Обнаружен конец семестра: {stats.get('last_lesson_date')}")
    
    return "\n".join(lines)


def format_parse_error(error: str) -> str:
    """Форматировать ошибку парсинга для уведомления"""
    return f"❌ Ошибка автопарсинга расписания\n\n{error[:200]}"
