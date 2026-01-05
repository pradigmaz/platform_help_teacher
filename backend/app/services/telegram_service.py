import secrets
import string
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User, Group, UserRole
from app.core.config import settings
from app.core.redis import get_redis

RELINK_TTL = 300  # 5 минут


async def generate_relink_code(user_id: UUID) -> str:
    """
    Генерирует код для перепривязки Telegram.
    Сохраняет маппинг relink:{code} -> user_id в Redis.
    """
    code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    
    redis = await get_redis()
    await redis.setex(f"relink:{code}", RELINK_TTL, str(user_id))
    
    return code


async def generate_otp(telegram_id: int) -> str:
    """
    Генерирует криптографически стойкий код и сохраняет маппинг CODE -> ID.
    """
    # FIX: secrets вместо random
    otp = ''.join(secrets.choice(string.digits) for _ in range(6))
    
    redis = await get_redis()
    
    # TTL 300 sec (5 min)
    await redis.setex(f"auth:{otp}", 300, str(telegram_id)) 
    
    return otp

async def process_start_command(
    db: AsyncSession, 
    social_id: int, 
    full_name: str, 
    username: str | None, 
    args: str | None
) -> str:
    # 0. СЦЕНАРИЙ: ПЕРЕПРИВЯЗКА (relink код)
    if args:
        code = args.strip().upper()
        redis = await get_redis()
        
        # Проверяем relink код
        relink_user_id = await redis.get(f"relink:{code}")
        if relink_user_id:
            # Удаляем код (одноразовый)
            await redis.delete(f"relink:{code}")
            
            # Проверяем, не занят ли этот telegram другим пользователем
            existing = await db.execute(select(User).where(User.social_id == social_id))
            existing_user = existing.scalar_one_or_none()
            
            if existing_user and str(existing_user.id) != relink_user_id:
                return "❌ Этот Telegram уже привязан к другому аккаунту."
            
            # Находим пользователя для перепривязки
            from uuid import UUID as UUIDType
            result = await db.execute(select(User).where(User.id == UUIDType(relink_user_id)))
            user = result.scalar_one_or_none()
            
            if not user:
                return "❌ Пользователь не найден."
            
            # Перепривязываем
            user.social_id = social_id
            user.username = username
            await db.commit()
            
            return f"✅ <b>Telegram перепривязан!</b>\nАккаунт: <b>{user.full_name}</b>"
    
    # 1. СЦЕНАРИЙ: ПЕРЕДАН КОД (персональный invite_code студента ИЛИ код группы)
    if args:
        code = args.strip().upper()
        
        # Сначала ищем по персональному invite_code студента
        result = await db.execute(select(User).where(User.invite_code == code))
        existing_student = result.scalar_one_or_none()
        
        if existing_student:
            # Привязываем Telegram к существующему студенту
            if existing_student.social_id and existing_student.social_id != social_id:
                return "❌ Этот код уже привязан к другому Telegram-аккаунту."
            
            existing_student.social_id = social_id
            existing_student.username = username
            existing_student.is_active = True
            await db.commit()
            
            # Получаем группу для сообщения
            group_result = await db.execute(select(Group).where(Group.id == existing_student.group_id))
            group = group_result.scalar_one_or_none()
            group_name = group.name if group else "Неизвестная"
            
            return f"🎉 <b>Привязка успешна!</b>\nВы: <b>{existing_student.full_name}</b>\nГруппа: <b>{group_name}</b>\n\nНажми /start чтобы получить код входа."
        
        # Иначе ищем по коду группы (для новых студентов)
        result = await db.execute(select(Group).where(Group.code == code))
        group = result.scalar_one_or_none()
        
        if not group:
            return "❌ Код не найден. Проверь правильность."

        result = await db.execute(select(User).where(User.social_id == social_id))
        user = result.scalar_one_or_none()

        if user:
            user.group_id = group.id
            user.full_name = full_name
            user.username = username
            await db.commit()
            return f"✅ Вы переведены в группу <b>{group.name}</b>!"
        else:
            new_user = User(
                social_id=social_id,
                full_name=full_name,
                username=username,
                role=UserRole.STUDENT,
                group_id=group.id,
                is_active=True
            )
            db.add(new_user)
            await db.commit()
            return f"🎉 <b>Регистрация успешна!</b>\nГруппа: <b>{group.name}</b>.\n\nНажми /start ещё раз, чтобы получить код входа."

    # 2. СЦЕНАРИЙ: ВХОД (OTP)
    else:
        result = await db.execute(select(User).where(User.social_id == social_id))
        user = result.scalar_one_or_none()

        if not user:
            return "👋 Привет! Я тебя не знаю. Пришли инвайт-код группы (например: <code>/start CODE123</code>)."
        
        otp = await generate_otp(social_id)
        
        # Ссылка для быстрого входа
        login_url = f"{settings.FRONTEND_URL}/auth/login?code={otp}"
        
        return (
            f"🔐 <b>Вход в систему</b>\n\n"
            f"Твой код: <code>{otp}</code>\n\n"
            f"🔗 <a href=\"{login_url}\">Войти в один клик</a>\n\n"
            f"⚠️ Код действует 5 минут. Никому не сообщай его."
        )