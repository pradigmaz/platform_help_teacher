"""
CRUD операции для предметов и связей преподаватель-предмет.
"""
import logging
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Subject, TeacherSubjectAssignment, User, Group

logger = logging.getLogger(__name__)


# === Subject CRUD ===

async def get_subject(db: AsyncSession, subject_id: UUID) -> Optional[Subject]:
    """Получить предмет по ID"""
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    return result.scalar_one_or_none()


async def get_subject_by_name(db: AsyncSession, name: str) -> Optional[Subject]:
    """Получить предмет по названию (case-insensitive)"""
    result = await db.execute(
        select(Subject).where(func.lower(Subject.name) == func.lower(name))
    )
    return result.scalar_one_or_none()


async def get_all_subjects(db: AsyncSession, active_only: bool = True) -> List[Subject]:
    """Получить все предметы"""
    query = select(Subject).order_by(Subject.name)
    if active_only:
        query = query.where(Subject.is_active == True)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_subject(
    db: AsyncSession,
    name: str,
    code: Optional[str] = None,
    description: Optional[str] = None
) -> Subject:
    """Создать предмет"""
    subject = Subject(name=name, code=code, description=description)
    db.add(subject)
    await db.flush()
    await db.refresh(subject)
    logger.info(f"Created subject: {name} (id={subject.id})")
    return subject


async def get_or_create_subject(
    db: AsyncSession,
    name: str,
    code: Optional[str] = None
) -> tuple[Subject, bool]:
    """Получить или создать предмет. Возвращает (subject, created)"""
    existing = await get_subject_by_name(db, name)
    if existing:
        return existing, False
    subject = await create_subject(db, name, code)
    return subject, True


# === TeacherSubjectAssignment CRUD ===

async def get_teacher_subjects(
    db: AsyncSession,
    teacher_id: UUID,
    semester: Optional[str] = None,
    active_only: bool = True
) -> List[TeacherSubjectAssignment]:
    """Получить все предметы преподавателя"""
    query = (
        select(TeacherSubjectAssignment)
        .options(selectinload(TeacherSubjectAssignment.subject))
        .options(selectinload(TeacherSubjectAssignment.group))
        .where(TeacherSubjectAssignment.teacher_id == teacher_id)
    )
    if semester:
        query = query.where(TeacherSubjectAssignment.semester == semester)
    if active_only:
        query = query.where(TeacherSubjectAssignment.is_active == True)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_subject_teachers(
    db: AsyncSession,
    subject_id: UUID,
    group_id: Optional[UUID] = None,
    active_only: bool = True
) -> List[TeacherSubjectAssignment]:
    """Получить всех преподавателей предмета"""
    query = (
        select(TeacherSubjectAssignment)
        .options(selectinload(TeacherSubjectAssignment.teacher))
        .where(TeacherSubjectAssignment.subject_id == subject_id)
    )
    if group_id:
        query = query.where(TeacherSubjectAssignment.group_id == group_id)
    if active_only:
        query = query.where(TeacherSubjectAssignment.is_active == True)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def assign_teacher_to_subject(
    db: AsyncSession,
    teacher_id: UUID,
    subject_id: UUID,
    group_id: Optional[UUID] = None,
    semester: Optional[str] = None
) -> TeacherSubjectAssignment:
    """Назначить преподавателя на предмет"""
    # Проверяем существующую запись
    query = select(TeacherSubjectAssignment).where(
        and_(
            TeacherSubjectAssignment.teacher_id == teacher_id,
            TeacherSubjectAssignment.subject_id == subject_id,
            TeacherSubjectAssignment.group_id == group_id,
            TeacherSubjectAssignment.semester == semester
        )
    )
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        if not existing.is_active:
            existing.is_active = True
            await db.flush()
        return existing
    
    assignment = TeacherSubjectAssignment(
        teacher_id=teacher_id,
        subject_id=subject_id,
        group_id=group_id,
        semester=semester
    )
    db.add(assignment)
    await db.flush()
    await db.refresh(assignment)
    logger.info(f"Assigned teacher {teacher_id} to subject {subject_id}")
    return assignment


async def get_or_create_assignment_from_schedule(
    db: AsyncSession,
    teacher_id: UUID,
    subject_name: str,
    group_id: UUID,
    semester: Optional[str] = None
) -> tuple[TeacherSubjectAssignment, bool]:
    """
    Создать связь преподаватель-предмет из данных расписания.
    Автоматически создаёт Subject если не существует.
    Возвращает (assignment, created)
    """
    subject, _ = await get_or_create_subject(db, subject_name)
    
    # Проверяем существующую связь
    query = select(TeacherSubjectAssignment).where(
        and_(
            TeacherSubjectAssignment.teacher_id == teacher_id,
            TeacherSubjectAssignment.subject_id == subject.id,
            TeacherSubjectAssignment.group_id == group_id,
            TeacherSubjectAssignment.semester == semester
        )
    )
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        return existing, False
    
    assignment = await assign_teacher_to_subject(
        db, teacher_id, subject.id, group_id, semester
    )
    return assignment, True
