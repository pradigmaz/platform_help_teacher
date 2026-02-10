"""Расписание преподавателя для ботов."""
import logging
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_schedule import schedule as crud_schedule
from app.models.schedule import DayOfWeek, ScheduleItem
from app.services.schedule_constants import LESSON_NUMBER_TO_TIME

from .constants import Platform
from .users import find_user_by_social_id

logger = logging.getLogger(__name__)

# Названия дней недели
DAY_NAMES = {
    DayOfWeek.MONDAY: "Понедельник",
    DayOfWeek.TUESDAY: "Вторник",
    DayOfWeek.WEDNESDAY: "Среда",
    DayOfWeek.THURSDAY: "Четверг",
    DayOfWeek.FRIDAY: "Пятница",
    DayOfWeek.SATURDAY: "Суббота",
}

# Типы занятий
LESSON_TYPE_EMOJI = {
    "lecture": "📖",
    "practice": "📝",
    "lab": "🔬",
}


def format_schedule_item(item: ScheduleItem) -> str:
    """Форматирует один элемент расписания."""
    time = LESSON_NUMBER_TO_TIME.get(item.lesson_number, f"{item.lesson_number} пара")
    emoji = LESSON_TYPE_EMOJI.get(item.lesson_type.value, "📚")

    group_name = item.group.name if item.group else "?"
    subject = item.subject or "Без предмета"
    room = f", ауд. {item.room}" if item.room else ""
    subgroup = f" (п/г {item.subgroup})" if item.subgroup else ""

    return f"{emoji} {time} — {subject}\n   {group_name}{subgroup}{room}"


def format_teacher_schedule(items: list[ScheduleItem], platform: Platform) -> str:
    """Форматирует расписание преподавателя для бота."""
    if not items:
        return "📅 У вас нет занятий в расписании."

    # Группируем по дням
    by_day: dict[DayOfWeek, list[ScheduleItem]] = defaultdict(list)
    for item in items:
        by_day[item.day_of_week].append(item)

    lines = ["📅 <b>Ваше расписание</b>\n"] if platform == "telegram" else ["📅 Ваше расписание\n"]

    # Сортируем дни по порядку
    day_order = [DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY,
                 DayOfWeek.THURSDAY, DayOfWeek.FRIDAY, DayOfWeek.SATURDAY]

    for day in day_order:
        if day not in by_day:
            continue

        day_name = DAY_NAMES[day]
        if platform == "telegram":
            lines.append(f"\n<b>{day_name}</b>")
        else:
            lines.append(f"\n{day_name}")

        # Сортируем по номеру пары
        day_items = sorted(by_day[day], key=lambda x: x.lesson_number)
        for item in day_items:
            lines.append(format_schedule_item(item))

    return "\n".join(lines)


async def process_schedule_command(
    db: AsyncSession,
    social_id: int,
    platform: Platform = "telegram"
) -> str | None:
    """Обработка команды /schedule для преподавателя. Возвращает None для студентов."""
    user = await find_user_by_social_id(db, social_id, platform)

    if not user:
        logger.warning(f"User not found for {platform} ID {social_id}")
        return None  # Не авторизован — игнорируем

    logger.info(f"User found: {user.id} ({user.full_name}), role: {user.role}")

    if user.role not in ("teacher", "admin"):
        logger.info(f"User {user.id} is not teacher/admin, ignoring")
        return None  # Студент — игнорируем

    items = await crud_schedule.get_by_teacher(db, user.id)
    logger.info(f"Found {len(items)} schedule items for teacher {user.id}")

    if items:
        for item in items:
            logger.debug(
                f"Schedule item: {item.day_of_week.value} #{item.lesson_number} "
                f"{item.subject} (active={item.is_active})"
            )

    return format_teacher_schedule(items, platform)
