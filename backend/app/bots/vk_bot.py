"""
VK Bot - Long Poll handler.
Работает без внешнего URL, сам опрашивает VK.
"""
import logging
import asyncio
import secrets

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services import bot_service

logger = logging.getLogger(__name__)

# Глобальные объекты VK
vk_session = None
vk = None
longpoll = None
_task = None
_running = False


def init_vk():
    """Инициализация VK API."""
    global vk_session, vk, longpoll
    
    if not settings.VK_BOT_TOKEN or not settings.VK_GROUP_ID:
        logger.warning("VK bot not configured (VK_BOT_TOKEN or VK_GROUP_ID missing)")
        return False
    
    try:
        vk_session = vk_api.VkApi(token=settings.VK_BOT_TOKEN)
        vk = vk_session.get_api()
        longpoll = VkBotLongPoll(vk_session, settings.VK_GROUP_ID)
        logger.info(f"VK bot initialized for group {settings.VK_GROUP_ID}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize VK bot: {e}")
        return False


def send_message_sync(user_id: int, message: str) -> bool:
    """Синхронная отправка сообщения."""
    global vk
    if not vk:
        return False
    try:
        vk.messages.send(
            user_id=user_id,
            message=message,
            random_id=secrets.randbelow(2**31) + 1
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send VK message: {e}")
        return False


def parse_command(text: str) -> tuple[str | None, str | None]:
    """Парсинг команды из текста."""
    if not text:
        return None, None
    text = text.strip()
    if text.startswith("/"):
        parts = text.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else None
        return command, args
    if text.lower() in ("начать", "start"):
        return "/start", None
    return None, text


async def handle_message(user_id: int, text: str):
    """Асинхронная обработка сообщения."""
    command, args = parse_command(text)
    response = None
    
    try:
        async with AsyncSessionLocal() as db:
            if command == "/start":
                response = await bot_service.process_start_command(
                    db=db,
                    social_id=user_id,
                    full_name="",
                    username=None,
                    args=args,
                    platform="vk"
                )
            elif command == "/status":
                response = "✅ Бот работает в штатном режиме."
            elif command == "/cancel":
                from app.core.redis import get_redis
                redis = await get_redis()
                await redis.delete(f"fsm:vk:{user_id}")
                response = "❌ Действие отменено."
            elif args:
                response = await bot_service.process_text_message(
                    db=db,
                    social_id=user_id,
                    text=args,
                    username=None,
                    platform="vk"
                )
    except Exception as e:
        logger.error(f"Error handling VK message: {e}", exc_info=True)
        response = "Произошла внутренняя ошибка сервера."
    
    if response:
        send_message_sync(user_id, response)


def _poll_once():
    """Один цикл опроса Long Poll (синхронный)."""
    global longpoll
    try:
        for event in longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                msg = event.obj.message
                user_id = msg.get("from_id")
                text = msg.get("text", "")
                
                if user_id and user_id > 0:
                    logger.info(f"VK message from {user_id}: {text[:50]}")
                    return (user_id, text)
    except Exception as e:
        logger.error(f"VK Long Poll error: {e}")
    return None


async def _longpoll_loop():
    """Асинхронный цикл Long Poll."""
    global _running
    
    logger.info("VK Long Poll loop started")
    loop = asyncio.get_event_loop()
    
    while _running:
        try:
            # Запускаем синхронный poll в executor
            result = await loop.run_in_executor(None, _poll_once)
            if result:
                user_id, text = result
                await handle_message(user_id, text)
        except Exception as e:
            logger.error(f"VK Long Poll loop error: {e}")
            if _running:
                await asyncio.sleep(5)


async def start_longpoll():
    """Запуск Long Poll."""
    global _running, _task
    
    if not init_vk():
        return
    
    _running = True
    _task = asyncio.create_task(_longpoll_loop())
    logger.info("VK Long Poll started in background")


async def stop_longpoll():
    """Остановка Long Poll."""
    global _running, _task
    _running = False
    if _task:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
    logger.info("VK Long Poll stopped")
