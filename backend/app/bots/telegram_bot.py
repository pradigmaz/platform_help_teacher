import logging
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, CommandObject
from aiogram.client.default import DefaultBotProperties
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services import telegram_service

logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(
    token=settings.TELEGRAM_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Диспетчер и роутер
dp = Dispatcher()
router = Router()

@router.message(CommandStart())
async def command_start_handler(message: types.Message, command: CommandObject) -> None:
    """
    Обработка команды /start.
    Принимает аргументы для диплинков (инвайт-коды).
    """
    social_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username
    args = command.args  # Например: "IS-24-TEST"

    logger.info(f"Received /start from user {social_id} ({username}) with args: {args}")

    try:
        async with AsyncSessionLocal() as db:
            response_text = await telegram_service.process_start_command(
                db=db,
                social_id=social_id,
                full_name=full_name,
                username=username,
                args=args
            )
            await message.answer(response_text)
    except Exception as e:
        logger.error(f"Error in command_start_handler: {e}", exc_info=True)
        await message.answer("Произошла внутренняя ошибка сервера.")

@router.message(lambda message: message.text == "/status")
async def command_status_handler(message: types.Message) -> None:
    """
    Проверка, что бот жив.
    """
    await message.answer("✅ Бот работает в штатном режиме.")

# Регистрируем роутер в диспетчере
dp.include_router(router)