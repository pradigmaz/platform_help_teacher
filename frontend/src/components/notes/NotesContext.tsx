'use client';

import { createContext, useContext, useState, useCallback, useEffect, useMemo, useRef, type ReactNode } from 'react';
import api from '@/lib/api';
import type { Note, EntityType, NoteColor } from '@/hooks/useNotes';

interface NotesContextValue {
  // Получить заметки для entity (из кэша)
  getNotes: (entityType: EntityType, entityId: string) => Note[];
  // Загрузить заметки для списка entity одним запросом
  loadNotesBatch: (entityType: EntityType, entityIds: string[]) => Promise<void>;
  // CRUD операции (обновляют кэш)
  createNote: (entityType: EntityType, entityId: string, content: string, color?: NoteColor, isPinned?: boolean) => Promise<Note | null>;
  updateNote: (noteId: string, data: { content?: string; color?: NoteColor; is_pinned?: boolean }) => Promise<Note | null>;
  deleteNote: (noteId: string, entityType: EntityType, entityId: string) => Promise<boolean>;
}

const NotesContext = createContext<NotesContextValue | null>(null);
const NotesActionsContext = createContext<Pick<NotesContextValue, 'loadNotesBatch' | 'createNote' | 'updateNote' | 'deleteNote'> | null>(null);

// Кэш: entityType:entityId -> notes[]
type NotesCache = Map<string, Note[]>;
const NOTES_BATCH_SIZE = 100;

function getCacheKey(entityType: EntityType, entityId: string): string {
  return `${entityType}:${entityId}`;
}

export function chunkEntityIds(entityIds: string[], size: number = NOTES_BATCH_SIZE): string[][] {
  const chunks: string[][] = [];

  for (let index = 0; index < entityIds.length; index += size) {
    chunks.push(entityIds.slice(index, index + size));
  }

  return chunks;
}

export function NotesProvider({ children }: { children: ReactNode }) {
  const [cache, setCache] = useState<NotesCache>(new Map());
  const cacheRef = useRef(cache);
  const inFlightRef = useRef<Set<string>>(new Set());
  const emptyNotesRef = useRef<Note[]>([]);

  useEffect(() => {
    cacheRef.current = cache;
  }, [cache]);

  const getNotes = useCallback((entityType: EntityType, entityId: string): Note[] => {
    return cache.get(getCacheKey(entityType, entityId)) || emptyNotesRef.current;
  }, [cache]);

  const loadNotesBatch = useCallback(async (entityType: EntityType, entityIds: string[]) => {
    if (entityIds.length === 0) return;

    const uniqueIds = [...new Set(entityIds)];
    const uncached = uniqueIds.filter((id) => {
      const key = getCacheKey(entityType, id);
      return !cacheRef.current.has(key) && !inFlightRef.current.has(key);
    });

    if (uncached.length === 0) return;

    uncached.forEach((id) => {
      inFlightRef.current.add(getCacheKey(entityType, id));
    });

    try {
      for (const entityIdChunk of chunkEntityIds(uncached)) {
        const { data } = await api.post(
          '/admin/notes/batch',
          { entity_ids: entityIdChunk },
          { params: { entity_type: entityType } }
        );

        setCache(prev => {
          const next = new Map(prev);
          for (const [entityId, notes] of Object.entries(data)) {
            next.set(getCacheKey(entityType, entityId), notes as Note[]);
          }
          return next;
        });
      }
    } catch (err) {
      console.error('Failed to load notes batch:', err);
    } finally {
      uncached.forEach((id) => {
        inFlightRef.current.delete(getCacheKey(entityType, id));
      });
    }
  }, []);

  const createNote = useCallback(async (
    entityType: EntityType,
    entityId: string,
    content: string,
    color: NoteColor = 'default',
    isPinned: boolean = false
  ): Promise<Note | null> => {
    try {
      const { data } = await api.post('/admin/notes/', {
        entity_type: entityType,
        entity_id: entityId,
        content,
        color,
        is_pinned: isPinned
      });
      
      setCache(prev => {
        const next = new Map(prev);
        const key = getCacheKey(entityType, entityId);
        const existing = next.get(key) || [];
        next.set(key, [data, ...existing]);
        return next;
      });
      
      return data;
    } catch {
      return null;
    }
  }, []);

  const updateNote = useCallback(async (
    noteId: string,
    data: { content?: string; color?: NoteColor; is_pinned?: boolean }
  ): Promise<Note | null> => {
    try {
      const { data: updated } = await api.patch(`/admin/notes/${noteId}`, data);
      
      setCache(prev => {
        const next = new Map(prev);
        for (const [key, notes] of next.entries()) {
          const idx = notes.findIndex(n => n.id === noteId);
          if (idx !== -1) {
            const newNotes = [...notes];
            newNotes[idx] = updated;
            next.set(key, newNotes);
            break;
          }
        }
        return next;
      });
      
      return updated;
    } catch {
      return null;
    }
  }, []);

  const deleteNote = useCallback(async (
    noteId: string,
    entityType: EntityType,
    entityId: string
  ): Promise<boolean> => {
    try {
      await api.delete(`/admin/notes/${noteId}`);
      
      setCache(prev => {
        const next = new Map(prev);
        const key = getCacheKey(entityType, entityId);
        const existing = next.get(key) || [];
        next.set(key, existing.filter(n => n.id !== noteId));
        return next;
      });
      
      return true;
    } catch {
      return false;
    }
  }, []);

  const actionsValue = useMemo(() => ({
    loadNotesBatch,
    createNote,
    updateNote,
    deleteNote,
  }), [createNote, deleteNote, loadNotesBatch, updateNote]);

  const value = useMemo(() => ({
    getNotes,
    ...actionsValue,
  }), [actionsValue, getNotes]);

  return (
    <NotesActionsContext.Provider value={actionsValue}>
      <NotesContext.Provider value={value}>
        {children}
      </NotesContext.Provider>
    </NotesActionsContext.Provider>
  );
}

export function useNotesContext() {
  const ctx = useContext(NotesContext);
  if (!ctx) {
    throw new Error('useNotesContext must be used within NotesProvider');
  }
  return ctx;
}

// Хук для опционального использования контекста (fallback на обычный useNotes)
export function useNotesContextOptional() {
  return useContext(NotesContext);
}

export function useNotesActionsContext() {
  const ctx = useContext(NotesActionsContext);
  if (!ctx) {
    throw new Error('useNotesActionsContext must be used within NotesProvider');
  }
  return ctx;
}
