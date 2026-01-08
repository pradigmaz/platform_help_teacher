"""
Константы для системы аудита.
"""
import enum
from typing import Set


class ActionType(str, enum.Enum):
    """Типы действий для логирования."""
    VIEW = "view"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    AUTH_LOGIN = "auth_login"
    AUTH_LOGOUT = "auth_logout"
    SUBMIT = "submit"          # Отправка на проверку (ready)
    CANCEL = "cancel"          # Отмена действия
    DOWNLOAD = "download"
    ERROR = "error"
    # Bot actions
    BOT_START = "bot_start"              # /start command
    BOT_AUTH = "bot_auth"                # OTP generation for login
    BOT_BIND = "bot_bind"                # Account binding
    BOT_RELINK = "bot_relink"            # Account relinking
    BOT_MESSAGE = "bot_message"          # Text message processing
    BOT_INVITE = "bot_invite"            # Invite code usage
    # Backup actions (admin-only, security-critical)
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"
    BACKUP_DELETE = "backup_delete"
    BACKUP_VERIFY = "backup_verify"


class EntityType(str, enum.Enum):
    """Типы сущностей."""
    PROFILE = "profile"
    LAB = "lab"
    LAB_DETAIL = "lab_detail"
    SUBMISSION = "submission"
    ATTENDANCE = "attendance"
    ATTESTATION = "attestation"
    LECTURE = "lecture"
    TEACHER_CONTACTS = "teacher_contacts"
    SEMESTER = "semester"
    AUTH = "auth"
    BOT = "bot"                # Bot interactions
    BACKUP = "backup"          # Database backups (security-critical)


# Поля, которые нужно маскировать в логах
SENSITIVE_FIELDS: Set[str] = {
    "password",
    "token",
    "access_token",
    "refresh_token",
    "otp",
    "secret",
    "api_key",
    "authorization",
    "cookie",
}

# Пути, которые НЕ нужно логировать
EXCLUDED_PATHS: Set[str] = {
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
}

# Префиксы путей для логирования (whitelist)
AUDIT_PATH_PREFIXES = (
    "/api/v1/student",
    "/api/v1/auth",
    "/api/v1/lectures",
    "/api/v1/labs",
    "/api/v1/admin/backups",  # Security-critical operations
)

# Максимальный размер body для логирования (bytes)
MAX_BODY_SIZE = 10 * 1024  # 10KB
