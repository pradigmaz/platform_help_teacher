import re
import json
import secrets
import string
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User, Group, UserRole
from app.core.config import settings
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

RELINK_TTL = 300  # 5 минут
FSM_TTL = 600  # 10 минут для FSM состояния


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
        
        # Иначе ищем по инвайт-коду группы (для новых студентов)
        result = await db.execute(select(Group).where(Group.invite_code == code))
        group = result.scalar_one_or_none()
        
        if not group:
            return "❌ Код не найден. Проверь правильность."

        # Проверяем, есть ли уже пользователь с этим telegram
        result = await db.execute(select(User).where(User.social_id == social_id))
        user = result.scalar_one_or_none()

        if user:
            user.group_id = group.id
            user.full_name = full_name
            user.username = username
            await db.commit()
            return f"✅ Вы переведены в группу <b>{group.name}</b>!"
        else:
            # Новый пользователь - запускаем FSM для ввода ФИО
            redis = await get_redis()
            fsm_data = json.dumps({"state": "waiting_fio", "group_id": str(group.id), "group_name": group.name})
            await redis.setex(f"fsm:{social_id}", FSM_TTL, fsm_data)
            
            return (
                f"👋 <b>Привязка к группе {group.name}</b>\n\n"
                f"Введите ваше ФИО точно как в списке группы:\n"
                f"<i>Например: Иванов Иван Иванович</i>"
            )

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


def normalize_fio(text: str) -> str:
    """Нормализация ФИО: каждое слово с заглавной."""
    text = text.strip()
    parts = text.split()
    return ' '.join(word.capitalize() for word in parts)


def fio_similarity(fio1: str, fio2: str) -> float:
    """
    Простое сравнение ФИО. Возвращает 0.0-1.0.
    Сравнивает по словам (фамилия, имя, отчество).
    """
    parts1 = fio1.lower().split()
    parts2 = fio2.lower().split()
    
    if not parts1 or not parts2:
        return 0.0
    
    # Точное совпадение
    if parts1 == parts2:
        return 1.0
    
    # Считаем совпавшие слова
    matches = sum(1 for p1 in parts1 if p1 in parts2)
    total = max(len(parts1), len(parts2))
    
    return matches / total if total > 0 else 0.0


async def find_student_by_fio(db: AsyncSession, group_id: str, input_fio: str) -> tuple[User | None, list[User]]:
    """
    Поиск студента по ФИО в группе.
    Возвращает (exact_match, similar_matches).
    """
    normalized_input = normalize_fio(input_fio)
    
    # Получаем всех студентов группы без привязки к Telegram
    result = await db.execute(
        select(User).where(
            User.group_id == UUID(group_id),
            User.role == UserRole.STUDENT,
            User.social_id.is_(None)  # Только непривязанные
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
        elif similarity >= 0.6:  # Похожие (2 из 3 слов совпали)
            similar.append(student)
    
    return exact_match, similar


async def process_text_message(
    db: AsyncSession,
    social_id: int,
    text: str,
    username: str | None
) -> str | None:
    """
    Обработка текстовых сообщений (не команд).
    Возвращает ответ или None если нет активного FSM состояния.
    """
    redis = await get_redis()
    fsm_raw = await redis.get(f"fsm:{social_id}")
    
    if not fsm_raw:
        return None
    
    try:
        fsm_data = json.loads(fsm_raw)
    except json.JSONDecodeError:
        await redis.delete(f"fsm:{social_id}")
        return None
    
    state = fsm_data.get("state")
    group_id = fsm_data.get("group_id")
    group_name = fsm_data.get("group_name", "")
    
    if state == "waiting_fio":
        # Валидация базовая
        text = text.strip()
        if not re.match(r'^[А-ЯЁа-яё\s\-]+$', text):
            return "❌ ФИО должно содержать только русские буквы\n\nВведите ФИО ещё раз:"
        
        parts = text.split()
        if len(parts) < 2:
            return "❌ Введите минимум фамилию и имя\n\nВведите ФИО ещё раз:"
        
        # Ищем студента в БД
        exact_match, similar = await find_student_by_fio(db, group_id, text)
        
        if exact_match:
            # Точное совпадение - привязываем
            exact_match.social_id = social_id
            exact_match.username = username
            await db.commit()
            await redis.delete(f"fsm:{social_id}")
            
            return (
                f"🎉 <b>Привязка успешна!</b>\n\n"
                f"Вы: <b>{exact_match.full_name}</b>\n"
                f"Группа: <b>{group_name}</b>\n\n"
                f"Нажми /start чтобы получить код входа."
            )
        
        if similar:
            # Есть похожие - предлагаем выбрать
            options = "\n".join(f"• {s.full_name}" for s in similar[:5])
            
            # Сохраняем похожих в FSM для возможного выбора
            fsm_data["similar_ids"] = [str(s.id) for s in similar[:5]]
            fsm_data["similar_names"] = [s.full_name for s in similar[:5]]
            fsm_data["state"] = "confirm_fio"
            await redis.setex(f"fsm:{social_id}", FSM_TTL, json.dumps(fsm_data))
            
            return (
                f"🤔 Точного совпадения не найдено.\n\n"
                f"Возможно, вы имели в виду:\n{options}\n\n"
                f"Введите ФИО точно как в списке, или напишите /cancel для отмены."
            )
        
        # Никого не нашли
        return (
            f"❌ Студент с таким ФИО не найден в группе <b>{group_name}</b>.\n\n"
            f"Проверьте правильность написания и попробуйте ещё раз.\n"
            f"Или напишите /cancel для отмены."
        )
    
    elif state == "confirm_fio":
        # Повторный ввод после показа похожих
        if text.strip().lower() == "/cancel":
            await redis.delete(f"fsm:{social_id}")
            return "❌ Регистрация отменена."
        
        # Ищем снова
        exact_match, similar = await find_student_by_fio(db, group_id, text)
        
        if exact_match:
            exact_match.social_id = social_id
            exact_match.username = username
            await db.commit()
            await redis.delete(f"fsm:{social_id}")
            
            return (
                f"🎉 <b>Привязка успешна!</b>\n\n"
                f"Вы: <b>{exact_match.full_name}</b>\n"
                f"Группа: <b>{group_name}</b>\n\n"
                f"Нажми /start чтобы получить код входа."
            )
        
        return (
            f"❌ Студент не найден. Введите ФИО точно как в списке группы.\n"
            f"Или напишите /cancel для отмены."
        )
    
    # Неизвестное состояние - сбрасываем
    await redis.delete(f"fsm:{social_id}")
    return None
