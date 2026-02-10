"""FSM диалоги для ботов (ввод ФИО)."""

import json
import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import log_bot_bind, log_bot_message
from app.core.redis import get_redis

from .constants import FSM_TTL, Platform
from .users import bind_social_id, find_student_by_fio

logger = logging.getLogger(__name__)

# Паттерн для валидации ФИО
FIO_PATTERN = re.compile(r"^[А-ЯЁа-яё\s\-]+$")


async def process_text_message(
    db: AsyncSession, social_id: int, text: str, username: str | None, platform: Platform = "telegram"
) -> str | None:
    """Обработка текстовых сообщений (FSM диалоги)."""
    redis = await get_redis()
    fsm_raw = await redis.get(f"fsm:{platform}:{social_id}")

    if not fsm_raw:
        return None

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
        return await _handle_waiting_fio(
            db, redis, social_id, text, username, platform, fsm_platform, fsm_data, group_id, group_name
        )

    elif state == "confirm_fio":
        return await _handle_confirm_fio(
            db, redis, social_id, text, username, platform, fsm_platform, group_id, group_name
        )

    await redis.delete(f"fsm:{platform}:{social_id}")
    return None


async def _handle_waiting_fio(
    db, redis, social_id, text, username, platform, fsm_platform, fsm_data, group_id, group_name
) -> str:
    """Обработка состояния waiting_fio."""
    text = text.strip()

    if text.lower() == "/cancel":
        await redis.delete(f"fsm:{platform}:{social_id}")
        return "❌ Регистрация отменена."

    if not FIO_PATTERN.match(text):
        return "❌ ФИО должно содержать только русские буквы\n\nВведите ФИО ещё раз или /cancel для отмены:"

    parts = text.split()
    if len(parts) < 2:
        return "❌ Введите минимум фамилию и имя\n\nВведите ФИО ещё раз или /cancel для отмены:"

    exact_match, similar = await find_student_by_fio(db, group_id, text)

    if exact_match:
        error = await bind_social_id(db, exact_match, social_id, fsm_platform, username)
        if error:
            await redis.delete(f"fsm:{platform}:{social_id}")
            return error
        await db.commit()
        await redis.delete(f"fsm:{platform}:{social_id}")

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


async def _handle_confirm_fio(
    db, redis, social_id, text, username, platform, fsm_platform, group_id, group_name
) -> str:
    """Обработка состояния confirm_fio."""
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

        await log_bot_bind(db, social_id, fsm_platform, exact_match.id, username, "fio_confirm")

        return f"🎉 Привязка успешна!\n\nВы: {exact_match.full_name}\nГруппа: {group_name}\n\nОтправьте /start для получения кода входа."

    return "❌ Студент не найден. Введите ФИО точно как в списке группы.\nИли напишите /cancel для отмены."
