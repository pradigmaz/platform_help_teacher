"""CRUD операции для заметок."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note, EntityType, NoteColor


class CRUDNote:
    async def get(self, db: AsyncSession, note_id: UUID) -> Optional[Note]:
        """Получить заметку по ID."""
        result = await db.execute(select(Note).where(Note.id == note_id))
        return result.scalar_one_or_none()

    async def get_by_entity(
        self, 
        db: AsyncSession, 
        entity_type: str, 
        entity_id: UUID
    ) -> List[Note]:
        """Получить все заметки для сущности."""
        result = await db.execute(
            select(Note)
            .where(and_(
                Note.entity_type == entity_type,
                Note.entity_id == entity_id
            ))
            .order_by(Note.is_pinned.desc(), Note.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: UUID,
        content: str,
        color: str = NoteColor.DEFAULT.value,
        is_pinned: bool = False,
        author_id: Optional[UUID] = None
    ) -> Note:
        """Создать заметку."""
        note = Note(
            entity_type=entity_type,
            entity_id=entity_id,
            content=content,
            color=color,
            is_pinned=is_pinned,
            author_id=author_id
        )
        db.add(note)
        await db.commit()
        await db.refresh(note)
        return note

    async def update(
        self,
        db: AsyncSession,
        note: Note,
        content: Optional[str] = None,
        color: Optional[str] = None,
        is_pinned: Optional[bool] = None
    ) -> Note:
        """Обновить заметку."""
        if content is not None:
            note.content = content
        if color is not None:
            note.color = color
        if is_pinned is not None:
            note.is_pinned = is_pinned
        
        await db.commit()
        await db.refresh(note)
        return note

    async def delete(self, db: AsyncSession, note_id: UUID) -> bool:
        """Удалить заметку."""
        note = await self.get(db, note_id)
        if note:
            await db.delete(note)
            await db.commit()
            return True
        return False

    async def delete_by_entity(
        self, 
        db: AsyncSession, 
        entity_type: str, 
        entity_id: UUID
    ) -> int:
        """Удалить все заметки для сущности."""
        notes = await self.get_by_entity(db, entity_type, entity_id)
        count = len(notes)
        for note in notes:
            await db.delete(note)
        await db.commit()
        return count


crud_note = CRUDNote()
