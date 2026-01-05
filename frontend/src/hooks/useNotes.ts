'use client';

import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';

export type EntityType = 'lesson' | 'student' | 'group' | 'work' | 'schedule_item';
export type NoteColor = 'default' | 'red' | 'orange' | 'yellow' | 'green' | 'blue' | 'purple';

export interface Note {
  id: string;
  entity_type: string;
  entity_id: string;
  content: string;
  color: NoteColor;
  is_pinned: boolean;
  author_id: string | null;
  created_at: string;
  updated_at: string;
}

interface UseNotesReturn {
  notes: Note[];
  isLoading: boolean;
  error: string | null;
  createNote: (content: string, color?: NoteColor, isPinned?: boolean) => Promise<Note | null>;
  updateNote: (noteId: string, data: { content?: string; color?: NoteColor; is_pinned?: boolean }) => Promise<Note | null>;
  deleteNote: (noteId: string) => Promise<boolean>;
  refresh: () => Promise<void>;
}

export function useNotes(entityType: EntityType, entityId: string): UseNotesReturn {
  const [notes, setNotes] = useState<Note[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadNotes = useCallback(async () => {
    if (!entityId) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const { data } = await api.get('/admin/notes/', {
        params: { entity_type: entityType, entity_id: entityId }
      });
      setNotes(data.notes || []);
    } catch (err) {
      setError('Ошибка загрузки заметок');
      setNotes([]);
    } finally {
      setIsLoading(false);
    }
  }, [entityType, entityId]);

  useEffect(() => {
    loadNotes();
  }, [loadNotes]);

  const createNote = useCallback(async (
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
      setNotes(prev => [data, ...prev]);
      return data;
    } catch {
      setError('Ошибка создания заметки');
      return null;
    }
  }, [entityType, entityId]);

  const updateNote = useCallback(async (
    noteId: string, 
    data: { content?: string; color?: NoteColor; is_pinned?: boolean }
  ): Promise<Note | null> => {
    try {
      const { data: updated } = await api.patch(`/admin/notes/${noteId}`, data);
      setNotes(prev => prev.map(n => n.id === noteId ? updated : n));
      return updated;
    } catch {
      setError('Ошибка обновления заметки');
      return null;
    }
  }, []);

  const deleteNote = useCallback(async (noteId: string): Promise<boolean> => {
    try {
      await api.delete(`/admin/notes/${noteId}`);
      setNotes(prev => prev.filter(n => n.id !== noteId));
      return true;
    } catch {
      setError('Ошибка удаления заметки');
      return false;
    }
  }, []);

  return {
    notes,
    isLoading,
    error,
    createNote,
    updateNote,
    deleteNote,
    refresh: loadNotes
  };
}
