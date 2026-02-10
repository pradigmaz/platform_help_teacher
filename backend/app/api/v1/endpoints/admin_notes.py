"""API endpoints для заметок."""
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud.crud_note import crud_note
from app.db.session import get_db
from app.models.note import Note
from app.models.user import User
from app.schemas.note import EntityType, NoteCreate, NoteResponse, NotesListResponse, NoteUpdate

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


@router.post("/batch")
async def get_notes_batch(
    entity_type: EntityType = Query(...),
    entity_ids: list[UUID] = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Получить заметки для нескольких сущностей одним запросом.
    Возвращает dict: {entity_id: [notes]}
    """
    if len(entity_ids) > 100:
        raise HTTPException(status_code=400, detail="Максимум 100 сущностей за раз")

    result = await db.execute(
        select(Note)
        .where(and_(
            Note.entity_type == entity_type.value,
            Note.entity_id.in_(entity_ids)
        ))
        .order_by(Note.is_pinned.desc(), Note.created_at.desc())
    )
    notes = list(result.scalars().all())

    # Группируем по entity_id
    grouped: dict[str, list] = {str(eid): [] for eid in entity_ids}
    for note in notes:
        eid = str(note.entity_id)
        if eid in grouped:
            grouped[eid].append({
                "id": str(note.id),
                "entity_type": note.entity_type,
                "entity_id": str(note.entity_id),
                "content": note.content,
                "color": note.color,
                "is_pinned": note.is_pinned,
                "author_id": str(note.author_id) if note.author_id else None,
                "created_at": note.created_at.isoformat(),
                "updated_at": note.updated_at.isoformat() if note.updated_at else note.created_at.isoformat(),
            })

    return grouped


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
