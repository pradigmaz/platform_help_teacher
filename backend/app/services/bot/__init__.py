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
from .constants import Platform, RELINK_TTL, FSM_TTL
from .rate_limit import check_code_rate_limit, increment_code_attempts, reset_code_attempts
from .auth import generate_relink_code, generate_otp
from .users import find_user_by_social_id, find_student_by_fio, bind_social_id, get_social_id_field
from .commands import process_start_command, process_code_command
from .fsm import process_text_message
from .schedule import process_schedule_command

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
