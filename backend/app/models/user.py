from sqlalchemy import Text, BigInteger, ForeignKey, Boolean, Enum as SAEnum, CheckConstraint, Index, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID, uuid4
from typing import Optional, TYPE_CHECKING
import enum
from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .group import Group
    from .submission import Submission
    from .work_submission import WorkSubmission
    from .schedule_parser_config import ScheduleParserConfig

# Enum для ролей - никаких хардкодных строк "admin" в коде!
class UserRole(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"

class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(full_name) <= 200", name="ck_users_full_name_len"),
        CheckConstraint("length(username) <= 100", name="ck_users_username_len"),
        CheckConstraint("length(invite_code) <= 8", name="ck_users_invite_code_len"),
        Index("ix_users_created_at", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    social_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True, nullable=True, index=True)
    group_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("groups.id"), nullable=True, index=True)
    
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Используем Enum в БД
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.STUDENT)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    invite_code: Mapped[Optional[str]] = mapped_column(Text, unique=True, nullable=True, index=True)
    
    # Подгруппа (1 или 2, null = не разделён)
    subgroup: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Onboarding завершён (ФИО введено + аттестация настроена)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Контакты преподавателя (только для TEACHER/ADMIN)
    contacts: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default='{}'
    )
    
    # Настройки видимости контактов
    contact_visibility: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default='{}'
    )
    
    # Настройки преподавателя (только для TEACHER/ADMIN)
    # hide_previous_semester: bool - скрывать прошлый семестр от студентов
    teacher_settings: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {"hide_previous_semester": True},
        server_default='{"hide_previous_semester": true}'
    )

    # Relationships
    group: Mapped[Optional["Group"]] = relationship(back_populates="users")
    submissions: Mapped[list["Submission"]] = relationship(back_populates="user")
    work_submissions: Mapped[list["WorkSubmission"]] = relationship(back_populates="user")
    parser_config: Mapped[Optional["ScheduleParserConfig"]] = relationship(back_populates="teacher")