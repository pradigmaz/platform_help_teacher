"""
Хелперы для работы с заметками.
"""
from typing import List, Dict
from uuid import UUID
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note, EntityType


async def get_students_notes(
    db: AsyncSession,
    student_ids: List[UUID],
    visible_only: bool = True
) -> Dict[UUID, List[str]]:
    """Получение заметок для студентов через полиморфную привязку."""
    query = select(Note).where(
        Note.entity_type == EntityType.STUDENT.value,
        Note.entity_id.in_(student_ids)
    )
    
    if visible_only and hasattr(Note, 'is_visible_in_report'):
        query = query.where(Note.is_visible_in_report == True)
    
    result = await db.execute(query)
    notes = result.scalars().all()
    
    notes_map = defaultdict(list)
    for note in notes:
        notes_map[note.entity_id].append(note.content)
    
    return dict(notes_map)


async def get_student_notes(
    db: AsyncSession,
    student_id: UUID,
    visible_only: bool = True
) -> List[Note]:
    """Получение заметок для студента через полиморфную привязку."""
    query = select(Note).where(
        Note.entity_type == EntityType.STUDENT.value,
        Note.entity_id == student_id
    )
    
    if visible_only and hasattr(Note, 'is_visible_in_report'):
        query = query.where(Note.is_visible_in_report == True)
    
    result = await db.execute(query)
    return list(result.scalars().all())
