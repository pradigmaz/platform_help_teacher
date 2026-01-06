from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Text, Integer, Enum as SQLEnum, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID, uuid4
from enum import Enum
from .base import Base, TimestampMixin

# Разрываем циклический импорт
if TYPE_CHECKING:
    from .user import User
    from .lecture import Lecture


class GradingScale(str, Enum):
    """Система оценивания"""
    FIVE = "5"      # 5-балльная
    TEN = "10"      # 10-балльная
    HUNDRED = "100" # 100-балльная


class Group(Base, TimestampMixin):
    __tablename__ = "groups"
    __table_args__ = (
        CheckConstraint("length(code) <= 20", name="ck_groups_code_len"),
        CheckConstraint("length(name) <= 100", name="ck_groups_name_len"),
        CheckConstraint("length(invite_code) <= 8", name="ck_groups_invite_code_len"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    
    # Инвайт-код группы для бота (рандомный, обновляемый)
    invite_code: Mapped[Optional[str]] = mapped_column(Text, unique=True, nullable=True, index=True)
    
    # Настройка деления на подгруппы
    has_subgroups: Mapped[bool] = mapped_column(default=True, server_default="true")
    
    # Настройки лабораторных
    labs_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=None)
    grading_scale: Mapped[Optional[GradingScale]] = mapped_column(
        SQLEnum(GradingScale, name='gradingscale', create_constraint=False, native_enum=False),
        nullable=True, default=GradingScale.TEN
    )
    default_max_grade: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=10)
    
    # Relationships
    users: Mapped[List["User"]] = relationship(back_populates="group")
    
    lectures: Mapped[List["Lecture"]] = relationship(
        secondary="lecture_groups",
        back_populates="groups"
    )