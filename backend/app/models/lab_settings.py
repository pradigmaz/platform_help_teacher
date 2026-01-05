from sqlalchemy import String, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid4
from enum import Enum
from .base import Base, TimestampMixin


class GradingScale(str, Enum):
    """Система оценивания"""
    FIVE = "5"
    TEN = "10"
    HUNDRED = "100"


class LabSettings(Base, TimestampMixin):
    """Глобальные настройки лабораторных работ"""
    __tablename__ = "lab_settings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    labs_count: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    grading_scale: Mapped[GradingScale] = mapped_column(
        SQLEnum(GradingScale, name='gradingscale', create_constraint=False, native_enum=False),
        default=GradingScale.TEN, nullable=False
    )
    default_max_grade: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
