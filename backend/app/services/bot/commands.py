"""Обработка команд /start и /code."""
import json
import logging
import asyncio
import time
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, Group
from app.core.config import settings
from app.core.redis import get_redis
from app.audit import log_bot_start, log_bot_auth, log_bot_bind
from app.utils.codes import mask_code

from .constants import Platform, CODE_PATTERN, FSM_TTL, MIN_RESPONSE_TIME
from .rate_limit import check_code_rate_limit, increment_code_attempts, reset_code_attempts
from .auth import generate_otp
from .users import find_user_by_social_id, bind_social_id, get_social_id_field

logger = logging.getLogger(__name__)


async def process_start_command(
    db: AsyncSession,
    social_id: int,
    username: str | None,
    platform: Platform = "telegram"
) -> str:
    """Обработка команды /start (только приветствие и OTP)."""
    await log_bot_start(db, social_id, platform, username, None)
    
    user = await find_user_by_social_id(db, social_id, platform)
    if not user:
        return "👋 Привет! Я тебя не знаю.\n\nДля привязки аккаунта используй команду /code с инвайт-кодом группы.\n\nПример: /code ABC123"
    
    otp = await generate_otp(social_id, platform)
    await log_bot_auth(db, social_id, platform, user.id, username)
    
    if user.role in ("admin", "teacher"):
        login_url = f"{settings.FRONTEND_URL}/auth/login#code={otp}"
    else:
        login_url = f"{settings.FRONTEND_URL}/#code={otp}"
    
    if platform == "telegram":
        return (
            f"🔐 <b>Вход в систему</b>\n\n"
            f"Твой код: <code>{otp}</code>\n\n"
            f"🔗 <a href=\"{login_url}\">Войти в один клик</a>\n\n"
            f"⚠️ Код действует 5 минут. Никому не сообщай его."
        )
    else:
        return f"🔐 Вход в систему\n\nТвой код: {otp}\n\n🔗 Войти: {login_url}\n\n⚠️ Код действует 5 минут."


async def process_code_command(
    db: AsyncSession,
    social_id: int,
    full_name: str,
    username: str | None,
    code: str,
    platform: Platform = "telegram"
) -> str:
    """Обработка команды /code (ввод инвайт-кодов, relink-кодов)."""
    start_time = time.monotonic()
    redis = await get_redis()
    
    # Rate limiting
    allowed, lockout_remaining = await check_code_rate_limit(social_id, platform)
    if not allowed:
        minutes = (lockout_remaining or 0) // 60 + 1
        return f"⏳ Слишком много попыток. Подождите {minutes} мин."
    
    # Валидация формата
    code = code.strip().upper()
    if not CODE_PATTERN.match(code):
        return "❌ Неверный формат кода. Код должен содержать 6-8 символов (A-Z, 0-9)."
    
    await log_bot_start(db, social_id, platform, username, mask_code(code))
    logger.info(f"Processing code {mask_code(code)} from {platform} user {social_id}")
    
    # Параллельные проверки для защиты от timing attack
    relink_task = redis.get(f"relink:{code}")
    user_task = db.execute(select(User).where(User.invite_code == code))
    group_task = db.execute(select(Group).where(Group.invite_code == code))
    
    relink_data, user_result, group_result = await asyncio.gather(
        relink_task, user_task, group_task
    )
    
    existing_student = user_result.scalar_one_or_none()
    group = group_result.scalar_one_or_none()
    
    response = await _process_code_result(
        db, redis, social_id, full_name, username, code, platform,
        relink_data, existing_student, group
    )
    
    # Гарантируем минимальное время ответа
    elapsed = time.monotonic() - start_time
    if elapsed < MIN_RESPONSE_TIME:
        await asyncio.sleep(MIN_RESPONSE_TIME - elapsed)
    
    return response


async def _process_code_result(
    db: AsyncSession,
    redis,
    social_id: int,
    full_name: str,
    username: str | None,
    code: str,
    platform: Platform,
    relink_data,
    existing_student: User | None,
    group: Group | None,
) -> str:
    """Обработка результатов проверки кода."""
    
    # 1. Relink код
    if relink_data:
        return await _handle_relink(db, redis, social_id, username, code, platform, relink_data)
    
    # 2. Персональный invite_code
    if existing_student:
        return await _handle_personal_invite(db, social_id, username, platform, existing_student)
    
    # 3. Групповой invite_code
    if group:
        return await _handle_group_invite(db, redis, social_id, full_name, username, platform, group)
    
    # 4. Код не найден
    remaining = await increment_code_attempts(social_id, platform)
    if remaining == 0:
        return "❌ Код не найден.\n\n⏳ Слишком много неудачных попыток. Подождите 15 минут."
    return f"❌ Код не найден. Проверьте правильность.\n\nОсталось попыток: {remaining}"


async def _handle_relink(db, redis, social_id, username, code, platform, relink_data) -> str:
    """Обработка relink-кода.
    
    SECURITY: Проверяет что код использует тот же пользователь, который его запросил.
    Если у аккаунта уже была привязка — код может использовать только владелец.
    """
    try:
        data = json.loads(relink_data)
        target_user_id = data.get("user_id")
        target_platform = data.get("platform", platform)
        original_social_id = data.get("original_social_id")  # SECURITY: ID владельца
    except json.JSONDecodeError:
        target_user_id = relink_data
        target_platform = platform
        original_social_id = None
    
    # SECURITY: Если у аккаунта была привязка, код может использовать только владелец
    if original_social_id is not None and original_social_id != social_id:
        logger.warning(
            f"SECURITY: Relink code theft attempt! "
            f"Code owner: {original_social_id}, attacker: {social_id}, code: {mask_code(code)}"
        )
        # НЕ удаляем код — владелец ещё может его использовать
        await increment_code_attempts(social_id, platform)
        return "❌ Этот код предназначен для другого аккаунта."
    
    await redis.delete(f"relink:{code}")
    await reset_code_attempts(social_id, platform)
    
    existing = await find_user_by_social_id(db, social_id, target_platform)
    if existing and str(existing.id) != target_user_id:
        return "❌ Этот аккаунт уже привязан к другому пользователю."
    
    result = await db.execute(select(User).where(User.id == UUID(target_user_id)))
    user = result.scalar_one_or_none()
    if not user:
        return "❌ Пользователь не найден."
    
    error = await bind_social_id(db, user, social_id, target_platform, username)
    if error:
        return error
    await db.commit()
    
    await log_bot_bind(db, social_id, target_platform, user.id, username, "relink")
    
    platform_name = "Telegram" if target_platform == "telegram" else "VK"
    return f"✅ {platform_name} привязан!\nПользователь: {user.full_name}"


async def _handle_personal_invite(db, social_id, username, platform, existing_student) -> str:
    """Обработка персонального invite_code."""
    await reset_code_attempts(social_id, platform)
    
    field = get_social_id_field(platform)
    current_value = getattr(existing_student, field.key)
    if current_value and current_value != social_id:
        return "❌ Этот код уже привязан к другому аккаунту."
    
    error = await bind_social_id(db, existing_student, social_id, platform, username)
    if error:
        return error
    existing_student.is_active = True
    await db.commit()
    
    await log_bot_bind(db, social_id, platform, existing_student.id, username, "invite")
    
    group_result = await db.execute(select(Group).where(Group.id == existing_student.group_id))
    student_group = group_result.scalar_one_or_none()
    group_name = student_group.name if student_group else "Неизвестная"
    return f"🎉 Привязка успешна!\nВы: {existing_student.full_name}\nГруппа: {group_name}\n\nОтправьте /start для получения кода входа."


async def _handle_group_invite(db, redis, social_id, full_name, username, platform, group) -> str:
    """Обработка группового invite_code."""
    await reset_code_attempts(social_id, platform)
    
    user = await find_user_by_social_id(db, social_id, platform)
    if user:
        user.group_id = group.id
        user.full_name = full_name or user.full_name
        user.username = username
        await db.commit()
        return f"✅ Вы переведены в группу {group.name}!"
    
    fsm_data = json.dumps({
        "state": "waiting_fio",
        "group_id": str(group.id),
        "group_name": group.name,
        "platform": platform
    })
    await redis.setex(f"fsm:{platform}:{social_id}", FSM_TTL, fsm_data)
    return f"👋 Привязка к группе {group.name}\n\nВведите ваше ФИО точно как в списке группы:\nНапример: Иванов Иван Иванович"
