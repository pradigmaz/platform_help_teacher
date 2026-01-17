"""
Обратная совместимость для bot_service.

Все функции перенесены в модуль app.services.bot.
Этот файл сохранён для совместимости с существующими импортами.
"""
# Re-export всё из нового модуля
from app.services.bot import (
    # Constants
    Platform,
    RELINK_TTL,
    FSM_TTL,
    # Rate limiting
    check_code_rate_limit,
    increment_code_attempts,
    reset_code_attempts,
    # Auth
    generate_relink_code,
    generate_otp,
    # Users
    find_user_by_social_id,
    find_student_by_fio,
    bind_social_id,
    get_social_id_field,
    # Commands
    process_start_command,
    process_code_command,
    # FSM
    process_text_message,
    # Schedule
    process_schedule_command,
)

__all__ = [
    "Platform",
    "RELINK_TTL",
    "FSM_TTL",
    "check_code_rate_limit",
    "increment_code_attempts",
    "reset_code_attempts",
    "generate_relink_code",
    "generate_otp",
    "find_user_by_social_id",
    "find_student_by_fio",
    "bind_social_id",
    "get_social_id_field",
    "process_start_command",
    "process_code_command",
    "process_text_message",
    "process_schedule_command",
]
