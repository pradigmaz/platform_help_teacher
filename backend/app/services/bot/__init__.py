"""
Сервисы для ботов (Telegram, VK).

Модули:
- constants: Константы и типы
- rate_limit: Rate limiting для команд
- auth: Генерация OTP и relink-кодов
- users: Поиск и привязка пользователей
- commands: Обработка команд /start, /code
- fsm: FSM диалоги (ввод ФИО)
- schedule: Расписание преподавателя
"""
from .auth import generate_otp, generate_relink_code
from .commands import process_code_command, process_start_command
from .constants import FSM_TTL, RELINK_TTL, Platform
from .fsm import process_text_message
from .rate_limit import check_code_rate_limit, increment_code_attempts, reset_code_attempts
from .schedule import process_schedule_command
from .users import bind_social_id, find_student_by_fio, find_user_by_social_id, get_social_id_field

__all__ = [
    # Constants
    "Platform",
    "RELINK_TTL",
    "FSM_TTL",
    # Rate limiting
    "check_code_rate_limit",
    "increment_code_attempts",
    "reset_code_attempts",
    # Auth
    "generate_relink_code",
    "generate_otp",
    # Users
    "find_user_by_social_id",
    "find_student_by_fio",
    "bind_social_id",
    "get_social_id_field",
    # Commands
    "process_start_command",
    "process_code_command",
    # FSM
    "process_text_message",
    # Schedule
    "process_schedule_command",
]
