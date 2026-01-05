"""API endpoints для заметок."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.session import get_db
from app.crud.crud_note import crud_note
from app.models.user import User
from app.schemas.note import (
    NoteCreate, 
    NoteUpdate, 
    NoteResponse, 
    NotesListResponse,
    EntityType
)

router = APIRouter()


@router.get("/", response_model=NotesListResponse)
async def get_notes(
    entity_type: EntityType = Query(...),
    entity_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Получить заметки для сущности."""
    notes = await crud_note.get_by_entity(db, entity_type.value, entity_id)
    return NotesListResponse(notes=notes, count=len(notes))


@router.post("/", response_model=NoteResponse)
async def create_note(
    note_in: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Создать заметку."""
    note = await crud_note.create(
        db,
        entity_type=note_in.entity_type.value,
        entity_id=note_in.entity_id,
        content=note_in.content,
        color=note_in.color.value,
        is_pinned=note_in.is_pinned,
        author_id=current_user.id
    )
    return note


@router.patch("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: UUID,
    note_in: NoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Обновить заметку."""
    note = await crud_note.get(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Заметка не найдена")
    
    note = await crud_note.update(
        db,
        note,
        content=note_in.content,
        color=note_in.color.value if note_in.color else None,
        is_pinned=note_in.is_pinned
    )
    return note


@router.delete("/{note_id}")
async def delete_note(
    note_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """Удалить заметку."""
    deleted = await crud_note.delete(db, note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Заметка не найдена")
    return {"status": "deleted"}
