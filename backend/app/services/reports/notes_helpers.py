"""
Хелперы для работы с заметками.
"""
from collections import defaultdict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import EntityType, Note


async def get_students_notes(
    db: AsyncSession,
    student_ids: list[UUID],
    visible_only: bool = True
) -> dict[UUID, list[str]]:
    """Получение заметок для студентов через полиморфную привязку."""
    query = select(Note).where(
        Note.entity_type == EntityType.STUDENT.value,
        Note.entity_id.in_(student_ids)
    )

    if visible_only and hasattr(Note, 'is_visible_in_report'):
        query = query.where(Note.is_visible_in_report)

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
) -> list[Note]:
    """Получение заметок для студента через полиморфную привязку."""
    query = select(Note).where(
        Note.entity_type == EntityType.STUDENT.value,
        Note.entity_id == student_id
    )

    if visible_only and hasattr(Note, 'is_visible_in_report'):
        query = query.where(Note.is_visible_in_report)

    result = await db.execute(query)
    return list(result.scalars().all())
