import logging

from aiogram import Bot, Dispatcher, Router, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject, CommandStart

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services import telegram_service

logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# Диспетчер и роутер
dp = Dispatcher()
router = Router()


def _extract_sender(message: types.Message) -> types.User | None:
    sender = message.from_user
    if sender is None:
        logger.warning("Telegram message without sender metadata received")
    return sender


@router.message(CommandStart())
async def command_start_handler(message: types.Message, command: CommandObject) -> None:
    """
    Обработка команды /start.
    Только приветствие и генерация OTP для авторизованных.
    Диплинки (/start CODE) перенаправляют на /code.
    """
    sender = _extract_sender(message)
    if sender is None:
        await message.answer("Не удалось определить отправителя сообщения.")
        return

    social_id = sender.id
    full_name = sender.full_name
    username = sender.username
    args = command.args  # Диплинк аргументы

    logger.info(f"Received /start from user {social_id} ({username}), deeplink={'yes' if args else 'no'}")

    # Если есть аргументы (диплинк) — обрабатываем как /code
    if args:
        try:
            async with AsyncSessionLocal() as db:
                response_text = await telegram_service.process_code_command(
                    db=db, social_id=social_id, full_name=full_name, username=username, code=args
                )
                await message.answer(response_text)
        except Exception as e:
            logger.error(f"Error in command_start_handler (deeplink): {e}", exc_info=True)
            await message.answer("Произошла внутренняя ошибка сервера.")
        return

    # Без аргументов — только приветствие/OTP
    try:
        async with AsyncSessionLocal() as db:
            response_text = await telegram_service.process_start_command(db=db, social_id=social_id, username=username)
            await message.answer(response_text)
    except Exception as e:
        logger.error(f"Error in command_start_handler: {e}", exc_info=True)
        await message.answer("Произошла внутренняя ошибка сервера.")


@router.message(Command("code"))
async def command_code_handler(message: types.Message, command: CommandObject) -> None:
    """
    Обработка команды /code <CODE>.
    Ввод инвайт-кодов, relink-кодов и т.д.
    """
    sender = _extract_sender(message)
    if sender is None:
        await message.answer("Не удалось определить отправителя сообщения.")
        return

    social_id = sender.id
    full_name = sender.full_name
    username = sender.username
    code = command.args

    code_hint = f"{code[:2]}***{code[-2:]}" if code and len(code) > 4 else "***"
    logger.info(f"Received /code from user {social_id} ({username}), code_hint={code_hint}")

    if not code:
        await message.answer("❌ Укажите код после команды.\n\nПример: /code ABC123")
        return

    try:
        async with AsyncSessionLocal() as db:
            response_text = await telegram_service.process_code_command(
                db=db, social_id=social_id, full_name=full_name, username=username, code=code
            )
            await message.answer(response_text)
    except Exception as e:
        logger.error(f"Error in command_code_handler: {e}", exc_info=True)
        await message.answer("Произошла внутренняя ошибка сервера.")


@router.message(lambda message: message.text == "/status")
async def command_status_handler(message: types.Message) -> None:
    """
    Проверка, что бот жив.
    """
    await message.answer("✅ Бот работает в штатном режиме.")


@router.message(Command("schedule"))
async def command_schedule_handler(message: types.Message) -> None:
    """
    Расписание преподавателя.
    """
    sender = _extract_sender(message)
    if sender is None:
        await message.answer("Не удалось определить отправителя сообщения.")
        return

    social_id = sender.id

    try:
        async with AsyncSessionLocal() as db:
            response_text = await telegram_service.process_schedule_command(db=db, social_id=social_id)
            if response_text:
                await message.answer(response_text)
    except Exception as e:
        logger.error(f"Error in command_schedule_handler: {e}", exc_info=True)
        await message.answer("Произошла внутренняя ошибка сервера.")


@router.message(lambda message: message.text and not message.text.startswith("/"))
async def text_message_handler(message: types.Message) -> None:
    """
    Обработка текстовых сообщений (FSM диалоги).
    """
    text = message.text
    sender = _extract_sender(message)
    if sender is None:
        await message.answer("Не удалось определить отправителя сообщения.")
        return
    if text is None:
        return

    social_id = sender.id
    username = sender.username

    try:
        async with AsyncSessionLocal() as db:
            response_text = await telegram_service.process_text_message(
                db=db, social_id=social_id, text=text, username=username
            )
            if response_text:
                await message.answer(response_text)
    except Exception as e:
        logger.error(f"Error in text_message_handler: {e}", exc_info=True)
        await message.answer("Произошла внутренняя ошибка сервера.")


# Регистрируем роутер в диспетчере
dp.include_router(router)
