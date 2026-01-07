"""Модель перевода студента между группами/подгруппами"""
from typing import Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, Date, Float, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID, uuid4
from datetime import date

from .base import Base, TimestampMixin
from .attestation_settings import AttestationType

if TYPE_CHECKING:
    from .user import User
    from .group import Group


class StudentTransfer(Base, TimestampMixin):
    """
    Запись о переводе студента между группами/подгруппами.
    Хранит снапшот данных студента на момент перевода для корректного расчёта аттестации.
    
    ВАЖНО: Снапшот создаётся ОДИН РАЗ при переводе и НЕ обновляется автоматически.
    Если данные в старой группе изменятся после перевода (исправление оценки),
    снапшот останется прежним. Это сделано намеренно для сохранения исторической
    точности на момент перевода.
    
    Для пересчёта снапшота используйте метод recalculate_snapshot() или
    создайте новую запись перевода.
    
    Атрибуты:
        attendance_data: Снапшот посещаемости {total_lessons, present, late, excused, absent}
        lab_grades_data: Снапшот оценок [{work_number, grade, lesson_id?}]
        activity_points: Сумма баллов активности на момент перевода
    """
    __tablename__ = "student_transfers"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    student_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Откуда
    from_group_id: Mapped[UUID] = mapped_column(ForeignKey("groups.id", ondelete="SET NULL"), nullable=True)
    from_subgroup: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Куда
    to_group_id: Mapped[UUID] = mapped_column(ForeignKey("groups.id", ondelete="SET NULL"), nullable=True)
    to_subgroup: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Дата перевода
    transfer_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Тип аттестации (для какого периода снапшот)
    attestation_type: Mapped[AttestationType] = mapped_column(
        SQLEnum(AttestationType, name='attestationtype', create_constraint=False, native_enum=False),
        nullable=False
    )
    
    # Снапшот посещаемости: {total_lessons, present, late, excused, absent}
    attendance_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    
    # Снапшот оценок за лабы: [{work_number, grade, lesson_id?}]
    lab_grades_data: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    
    # Сумма баллов активности
    activity_points: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    
    # Кто создал запись
    created_by_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    student: Mapped["User"] = relationship("User", foreign_keys=[student_id], lazy="joined")
    from_group: Mapped[Optional["Group"]] = relationship("Group", foreign_keys=[from_group_id])
    to_group: Mapped[Optional["Group"]] = relationship("Group", foreign_keys=[to_group_id])
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id])
