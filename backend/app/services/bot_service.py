"""
Общий сервис для ботов (Telegram, VK).
Platform-agnostic логика авторизации и FSM.
"""
import re
import json
import secrets
import string
import logging
from typing import Literal
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models import User, Group, UserRole
from app.core.config import settings
from app.core.redis import get_redis
from app.audit import log_bot_start, log_bot_auth, log_bot_bind, log_bot_message

from app.utils.text import normalize_fio, fio_similarity

logger = logging.getLogger(__name__)

RELINK_TTL = 300  # 5 минут
FSM_TTL = 600  # 10 минут для FSM состояния

Platform = Literal["telegram", "vk"]


async def generate_relink_code(user_id: UUID, platform: Platform) -> str:
    """Генерирует код для привязки/перепривязки аккаунта."""
    code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    redis = await get_redis()
    data = json.dumps({"user_id": str(user_id), "platform": platform})
    await redis.setex(f"relink:{code}", RELINK_TTL, data)
    return code


async def generate_otp(social_id: int, platform: Platform) -> str:
    """Генерирует OTP код для входа."""
    otp = ''.join(secrets.choice(string.digits) for _ in range(6))
    redis = await get_redis()
    data = json.dumps({"social_id": social_id, "platform": platform})
    await redis.setex(f"auth:{otp}", 300, data)
    return otp


def get_social_id_field(platform: Platform):
    """Возвращает поле модели для платформы."""
    return User.telegram_id if platform == "telegram" else User.vk_id


async def find_user_by_social_id(db: AsyncSession, social_id: int, platform: Platform) -> User | None:
    """Поиск пользователя по social_id для конкретной платформы."""
    field = get_social_id_field(platform)
    result = await db.execute(select(User).where(field == social_id))
    return result.scalar_one_or_none()


async def find_student_by_fio(db: AsyncSession, group_id: str, input_fio: str) -> tuple[User | None, list[User]]:
    """Поиск студента по ФИО в группе."""
    normalized_input = normalize_fio(input_fio)
    result = await db.execute(
        select(User).where(
            User.group_id == UUID(group_id),
            User.role == UserRole.STUDENT,
            User.telegram_id.is_(None),
            User.vk_id.is_(None)
        )
    )
    students = result.scalars().all()
    
    exact_match = None
    similar = []
    
    for student in students:
        similarity = fio_similarity(normalized_input, student.full_name)
        if similarity == 1.0:
            exact_match = student
            break
        elif similarity >= 0.6:
            similar.append(student)
    
    return exact_match, similar


async def bind_social_id(
    db: AsyncSession,
    user: User, 
    social_id: int, 
    platform: Platform, 
    username: str | None = None
) -> str | None:
    """
    Привязывает social_id к пользователю.
    
    Returns:
        None если успешно, строка с ошибкой если social_id уже занят.
    """
    # Проверка: не привязан ли этот social_id к другому пользователю
    existing = await find_user_by_social_id(db, social_id, platform)
    if existing and existing.id != user.id:
        platform_name = "Telegram" if platform == "telegram" else "VK"
        logger.warning(
            f"Попытка привязки занятого {platform_name} ID {social_id} "
            f"к пользователю {user.id} ({user.full_name}), "
            f"уже привязан к {existing.id} ({existing.full_name})"
        )
        return f"❌ Этот {platform_name} аккаунт уже привязан к другому пользователю."
    
    if platform == "telegram":
        user.telegram_id = social_id
        if username is not None:
            user.username = username
    else:
        user.vk_id = social_id
    
    return None


async def process_start_command(
    db: AsyncSession,
    social_id: int,
    full_name: str,
    username: str | None,
    args: str | None,
    platform: Platform = "telegram"
) -> str:
    """Обработка команды /start (общая для TG и VK)."""
    redis = await get_redis()
    
    # Логируем /start
    await log_bot_start(db, social_id, platform, username, args)
    
    # СЦЕНАРИЙ: КОД (relink, персональный или групповой)
    if args:
        code = args.strip().upper()
        
        # 1. Проверяем relink код (привязка/перепривязка)
        relink_data = await redis.get(f"relink:{code}")
        if relink_data:
            try:
                data = json.loads(relink_data)
                target_user_id = data.get("user_id")
                target_platform = data.get("platform", platform)
            except json.JSONDecodeError:
                target_user_id = relink_data  # старый формат
                target_platform = platform
            
            await redis.delete(f"relink:{code}")
            
            # Проверяем, не занят ли этот social_id другим пользователем
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
            
            # Логируем relink
            await log_bot_bind(db, social_id, target_platform, user.id, username, "relink")
            
            platform_name = "Telegram" if target_platform == "telegram" else "VK"
            return f"✅ {platform_name} привязан!\nПользователь: {user.full_name}"
        
        # 2. Персональный invite_code
        result = await db.execute(select(User).where(User.invite_code == code))
        existing_student = result.scalar_one_or_none()
        if existing_student:
            # Проверяем, не занят ли этот social_id
            field = get_social_id_field(platform)
            current_value = getattr(existing_student, field.key)
            if current_value and current_value != social_id:
                return "❌ Этот код уже привязан к другому аккаунту."
            
            error = await bind_social_id(db, existing_student, social_id, platform, username)
            if error:
                return error
            existing_student.is_active = True
            await db.commit()
            
            # Логируем привязку по invite_code
            await log_bot_bind(db, social_id, platform, existing_student.id, username, "invite")
            
            group_result = await db.execute(select(Group).where(Group.id == existing_student.group_id))
            group = group_result.scalar_one_or_none()
            group_name = group.name if group else "Неизвестная"
            return f"🎉 Привязка успешна!\nВы: {existing_student.full_name}\nГруппа: {group_name}\n\nОтправьте /start для получения кода входа."
        
        # Групповой invite_code
        result = await db.execute(select(Group).where(Group.invite_code == code))
        group = result.scalar_one_or_none()
        if not group:
            return "❌ Код не найден. Проверьте правильность."
        
        # Проверяем, есть ли уже пользователь с этим social_id
        user = await find_user_by_social_id(db, social_id, platform)
        if user:
            user.group_id = group.id
            user.full_name = full_name or user.full_name
            user.username = username
            await db.commit()
            return f"✅ Вы переведены в группу {group.name}!"
        else:
            # Новый пользователь - запускаем FSM для ввода ФИО
            fsm_data = json.dumps({
                "state": "waiting_fio",
                "group_id": str(group.id),
                "group_name": group.name,
                "platform": platform
            })
            await redis.setex(f"fsm:{platform}:{social_id}", FSM_TTL, fsm_data)
            return f"👋 Привязка к группе {group.name}\n\nВведите ваше ФИО точно как в списке группы:\nНапример: Иванов Иван Иванович"
    
    # СЦЕНАРИЙ: ВХОД (OTP)
    user = await find_user_by_social_id(db, social_id, platform)
    if not user:
        return "👋 Привет! Я тебя не знаю. Пришли инвайт-код группы (например: /start CODE123)."
    
    otp = await generate_otp(social_id, platform)
    
    # Логируем генерацию OTP
    await log_bot_auth(db, social_id, platform, user.id, username)
    
    # Разные URL для разных ролей
    if user.role in ("admin", "teacher"):
        login_url = f"{settings.FRONTEND_URL}/auth/login?code={otp}"
    else:
        login_url = f"{settings.FRONTEND_URL}/?code={otp}"
    
    if platform == "telegram":
        # HTML разметка для Telegram
        return (
            f"🔐 <b>Вход в систему</b>\n\n"
            f"Твой код: <code>{otp}</code>\n\n"
            f"🔗 <a href=\"{login_url}\">Войти в один клик</a>\n\n"
            f"⚠️ Код действует 5 минут. Никому не сообщай его."
        )
    else:
        # Простой текст для VK
        return f"🔐 Вход в систему\n\nТвой код: {otp}\n\n🔗 Войти: {login_url}\n\n⚠️ Код действует 5 минут."


async def process_text_message(
    db: AsyncSession,
    social_id: int,
    text: str,
    username: str | None,
    platform: Platform = "telegram"
) -> str | None:
    """Обработка текстовых сообщений (FSM диалоги)."""
    redis = await get_redis()
    fsm_raw = await redis.get(f"fsm:{platform}:{social_id}")
    
    if not fsm_raw:
        return None
    
    # Логируем текстовое сообщение
    await log_bot_message(db, social_id, platform, text, username, "fsm")
    
    try:
        fsm_data = json.loads(fsm_raw)
    except json.JSONDecodeError:
        await redis.delete(f"fsm:{platform}:{social_id}")
        return None
    
    state = fsm_data.get("state")
    group_id = fsm_data.get("group_id")
    group_name = fsm_data.get("group_name", "")
    fsm_platform = fsm_data.get("platform", platform)
    
    if state == "waiting_fio":
        text = text.strip()
        if not re.match(r'^[А-ЯЁа-яё\s\-]+$', text):
            return "❌ ФИО должно содержать только русские буквы\n\nВведите ФИО ещё раз:"
        
        parts = text.split()
        if len(parts) < 2:
            return "❌ Введите минимум фамилию и имя\n\nВведите ФИО ещё раз:"
        
        exact_match, similar = await find_student_by_fio(db, group_id, text)
        
        if exact_match:
            error = await bind_social_id(db, exact_match, social_id, fsm_platform, username)
            if error:
                await redis.delete(f"fsm:{platform}:{social_id}")
                return error
            await db.commit()
            await redis.delete(f"fsm:{platform}:{social_id}")
            
            # Логируем привязку через FSM (waiting_fio)
            await log_bot_bind(db, social_id, fsm_platform, exact_match.id, username, "fio_match")
            
            return f"🎉 Привязка успешна!\n\nВы: {exact_match.full_name}\nГруппа: {group_name}\n\nОтправьте /start для получения кода входа."
        
        if similar:
            options = "\n".join(f"• {s.full_name}" for s in similar[:5])
            fsm_data["similar_ids"] = [str(s.id) for s in similar[:5]]
            fsm_data["similar_names"] = [s.full_name for s in similar[:5]]
            fsm_data["state"] = "confirm_fio"
            await redis.setex(f"fsm:{platform}:{social_id}", FSM_TTL, json.dumps(fsm_data))
            return f"🤔 Точного совпадения не найдено.\n\nВозможно, вы имели в виду:\n{options}\n\nВведите ФИО точно как в списке, или напишите /cancel для отмены."
        
        return f"❌ Студент с таким ФИО не найден в группе {group_name}.\n\nПроверьте правильность написания и попробуйте ещё раз.\nИли напишите /cancel для отмены."
    
    elif state == "confirm_fio":
        if text.strip().lower() == "/cancel":
            await redis.delete(f"fsm:{platform}:{social_id}")
            return "❌ Регистрация отменена."
        
        exact_match, _ = await find_student_by_fio(db, group_id, text)
        if exact_match:
            error = await bind_social_id(db, exact_match, social_id, fsm_platform, username)
            if error:
                await redis.delete(f"fsm:{platform}:{social_id}")
                return error
            await db.commit()
            await redis.delete(f"fsm:{platform}:{social_id}")
            
            # Логируем привязку через FSM (confirm_fio)
            await log_bot_bind(db, social_id, fsm_platform, exact_match.id, username, "fio_confirm")
            
            return f"🎉 Привязка успешна!\n\nВы: {exact_match.full_name}\nГруппа: {group_name}\n\nОтправьте /start для получения кода входа."
        
        return f"❌ Студент не найден. Введите ФИО точно как в списке группы.\nИли напишите /cancel для отмены."
    
    await redis.delete(f"fsm:{platform}:{social_id}")
    return None
