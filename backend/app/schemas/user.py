from typing import Optional, Literal
from uuid import UUID
from pydantic import BaseModel, Field
from app.models import UserRole # Импортируем Enum из моделей

# Teacher contacts types
ContactVisibility = Literal["student", "report", "both", "none"]

class UserCreate(BaseModel):
    telegram_id: Optional[int] = None
    vk_id: Optional[int] = None
    full_name: str
    username: Optional[str] = None
    role: UserRole = UserRole.STUDENT
    group_code: Optional[str] = None

class UserResponse(BaseModel):
    id: UUID
    telegram_id: Optional[int] = None
    vk_id: Optional[int] = None
    full_name: str
    username: Optional[str]
    role: UserRole
    group_id: Optional[UUID]
    is_active: bool
    invite_code: Optional[str] = None
    onboarding_completed: bool = False

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    onboarding_completed: Optional[bool] = None

class StudentInGroup(BaseModel):
    """Студент в контексте группы"""
    id: UUID
    full_name: str
    username: Optional[str] = None
    invite_code: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


# ============ Teacher Contacts Schemas ============

class TeacherContacts(BaseModel):
    """Контактные данные преподавателя (только мессенджеры)."""
    telegram: Optional[str] = Field(None, max_length=100)
    vk: Optional[str] = Field(None, max_length=100)
    max: Optional[str] = Field(None, max_length=100)


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
    telegram: Optional[str] = None
    vk: Optional[str] = None
    max: Optional[str] = None
    teacher_name: Optional[str] = None


# ============ Relink Telegram Schemas ============

class RelinkTelegramResponse(BaseModel):
    """Ответ с кодом для перепривязки Telegram."""
    code: str
    expires_in: int = Field(description="Время жизни кода в секундах")
