import unicodedata
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models import UserRole  # Импортируем Enum из моделей

# Teacher contacts types
ContactVisibility = Literal["student", "report", "both", "none"]


def validate_full_name(name: str) -> str:
    """Валидация ФИО — только буквы, пробелы, дефисы, апострофы."""
    name = " ".join(name.split())  # Нормализуем пробелы
    if len(name) < 2:
        raise ValueError("ФИО должно содержать минимум 2 символа")
    if len(name) > 200:
        raise ValueError("ФИО не должно превышать 200 символов")

    # Проверяем каждый символ
    for char in name:
        if char in " -'":
            continue
        category = unicodedata.category(char)
        if category not in ("Lu", "Ll", "Lt", "Lm", "Lo"):  # Letter categories
            raise ValueError("ФИО может содержать только буквы, пробелы и дефисы")

    return name


class UserCreate(BaseModel):
    telegram_id: int | None = None
    vk_id: int | None = None
    full_name: str
    username: str | None = None
    role: UserRole = UserRole.STUDENT
    group_code: str | None = None


class UserResponse(BaseModel):
    id: UUID
    telegram_id: int | None = None
    vk_id: int | None = None
    full_name: str
    username: str | None
    role: UserRole
    group_id: UUID | None
    is_active: bool
    invite_code: str | None = None
    onboarding_completed: bool = False

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=200)
    onboarding_completed: bool | None = None

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return validate_full_name(v)


class StudentInGroup(BaseModel):
    """Студент в контексте группы"""

    id: UUID
    full_name: str
    username: str | None = None
    invite_code: str | None = None
    is_active: bool = True

    class Config:
        from_attributes = True


# ============ Teacher Contacts Schemas ============


class TeacherContacts(BaseModel):
    """Контактные данные преподавателя (только мессенджеры)."""

    telegram: str | None = Field(None, max_length=100)
    vk: str | None = Field(None, max_length=100)
    max: str | None = Field(None, max_length=100)


class ContactVisibilitySettings(BaseModel):
    """Настройки видимости для каждого контакта."""

    telegram: ContactVisibility = "none"
    vk: ContactVisibility = "none"
    max: ContactVisibility = "none"


class TeacherContactsUpdate(BaseModel):
    """Запрос обновления контактов."""

    contacts: TeacherContacts
    visibility: ContactVisibilitySettings


class TeacherContactsResponse(BaseModel):
    """Ответ с контактами преподавателя."""

    contacts: TeacherContacts
    visibility: ContactVisibilitySettings


class PublicTeacherContacts(BaseModel):
    """Контакты для публичного отображения (отфильтрованные)."""

    telegram: str | None = None
    vk: str | None = None
    max: str | None = None
    teacher_name: str | None = None


# ============ Relink Telegram Schemas ============


class RelinkTelegramResponse(BaseModel):
    """Ответ с кодом для перепривязки Telegram."""

    code: str
    expires_in: int = Field(description="Время жизни кода в секундах")
