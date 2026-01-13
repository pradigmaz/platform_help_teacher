'use client';

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
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
  // Статус загрузки
  isLoading: boolean;
}

const NotesContext = createContext<NotesContextValue | null>(null);

// Кэш: entityType:entityId -> notes[]
type NotesCache = Map<string, Note[]>;

function getCacheKey(entityType: EntityType, entityId: string): string {
  return `${entityType}:${entityId}`;
}

export function NotesProvider({ children }: { children: ReactNode }) {
  const [cache, setCache] = useState<NotesCache>(new Map());
  const [isLoading, setIsLoading] = useState(false);

  const getNotes = useCallback((entityType: EntityType, entityId: string): Note[] => {
    return cache.get(getCacheKey(entityType, entityId)) || [];
  }, [cache]);

  const loadNotesBatch = useCallback(async (entityType: EntityType, entityIds: string[]) => {
    if (entityIds.length === 0) return;
    
    // Фильтруем уже загруженные
    const uncached = entityIds.filter(id => !cache.has(getCacheKey(entityType, id)));
    if (uncached.length === 0) return;

    setIsLoading(true);
    try {
      const { data } = await api.post('/admin/notes/batch', 
        { entity_ids: uncached },
        { params: { entity_type: entityType } }
      );
      
      setCache(prev => {
        const next = new Map(prev);
        for (const [entityId, notes] of Object.entries(data)) {
          next.set(getCacheKey(entityType, entityId), notes as Note[]);
        }
        return next;
      });
    } catch (err) {
      console.error('Failed to load notes batch:', err);
    } finally {
      setIsLoading(false);
    }
  }, [cache]);

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

  return (
    <NotesContext.Provider value={{
      getNotes,
      loadNotesBatch,
      createNote,
      updateNote,
      deleteNote,
      isLoading
    }}>
      {children}
    </NotesContext.Provider>
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
