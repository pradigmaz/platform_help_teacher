"""
Модель предмета (дисциплины).
"""
from typing import Optional, List, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import String, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .teacher_subject import TeacherSubjectAssignment


class Subject(Base, TimestampMixin):
    """
    Справочник предметов (дисциплин).
    
    Примеры:
    - Компьютерные сети
    - Численные методы
    - Тестирование ИС
    """
    __tablename__ = "subjects"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # КС, ЧМ, ТИС
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    teacher_assignments: Mapped[List["TeacherSubjectAssignment"]] = relationship(
        back_populates="subject",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_subjects_name_lower', 'name'),
    )
