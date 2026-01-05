'use client';

import { useState } from 'react';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { StickyNote, Plus, Trash2, Pin, PinOff, Calendar } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useNotes, type EntityType, type NoteColor, type Note } from '@/hooks/useNotes';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

const NOTE_COLORS: { value: NoteColor; label: string; bg: string; dot: string }[] = [
  { value: 'default', label: 'Без цвета', bg: 'bg-muted', dot: 'bg-muted-foreground' },
  { value: 'red', label: 'Красный', bg: 'bg-red-100 dark:bg-red-900/40', dot: 'bg-red-500' },
  { value: 'orange', label: 'Оранжевый', bg: 'bg-orange-100 dark:bg-orange-900/40', dot: 'bg-orange-500' },
  { value: 'yellow', label: 'Жёлтый', bg: 'bg-yellow-100 dark:bg-yellow-900/40', dot: 'bg-yellow-500' },
  { value: 'green', label: 'Зелёный', bg: 'bg-green-100 dark:bg-green-900/40', dot: 'bg-green-500' },
  { value: 'blue', label: 'Синий', bg: 'bg-blue-100 dark:bg-blue-900/40', dot: 'bg-blue-500' },
  { value: 'purple', label: 'Фиолетовый', bg: 'bg-purple-100 dark:bg-purple-900/40', dot: 'bg-purple-500' },
];

interface NoteButtonProps {
  entityType: EntityType;
  entityId: string;
  size?: 'sm' | 'md';
  className?: string;
}

export function NoteButton({ entityType, entityId, size = 'sm', className }: NoteButtonProps) {
  const { notes, createNote, updateNote, deleteNote } = useNotes(entityType, entityId);
  const [isOpen, setIsOpen] = useState(false);
  const [newNoteText, setNewNoteText] = useState('');
  const [newNoteColor, setNewNoteColor] = useState<NoteColor>('default');
  const [editingNote, setEditingNote] = useState<Note | null>(null);

  const handleCreate = async () => {
    if (!newNoteText.trim()) return;
    await createNote(newNoteText.trim(), newNoteColor);
    setNewNoteText('');
    setNewNoteColor('default');
  };

  const handleUpdate = async () => {
    if (!editingNote || !newNoteText.trim()) return;
    await updateNote(editingNote.id, { content: newNoteText.trim(), color: newNoteColor });
    setEditingNote(null);
    setNewNoteText('');
    setNewNoteColor('default');
  };

  const handleDelete = async (noteId: string) => {
    await deleteNote(noteId);
  };

  const handleTogglePin = async (note: Note) => {
    await updateNote(note.id, { is_pinned: !note.is_pinned });
  };

  const startEdit = (note: Note) => {
    setEditingNote(note);
    setNewNoteText(note.content);
    setNewNoteColor(note.color);
  };

  const cancelEdit = () => {
    setEditingNote(null);
    setNewNoteText('');
    setNewNoteColor('default');
  };

  const getColorConfig = (color: NoteColor) => 
    NOTE_COLORS.find(c => c.value === color) || NOTE_COLORS[0];

  const hasNotes = notes.length > 0;
  const iconSize = size === 'sm' ? 'h-3.5 w-3.5' : 'h-4 w-4';
  const buttonSize = size === 'sm' ? 'h-5 w-5' : 'h-6 w-6';

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className={cn(
            buttonSize,
            'relative transition-all',
            hasNotes 
              ? 'text-yellow-500 hover:text-yellow-600 hover:scale-110' 
              : 'text-muted-foreground/50 hover:text-muted-foreground hover:scale-110 hover:bg-accent',
            className
          )}
          onClick={(e) => e.stopPropagation()}
        >
          <StickyNote className={iconSize} />
          {hasNotes && (
            <span className="absolute -top-0.5 -right-0.5 h-2 w-2 rounded-full bg-yellow-500 animate-pulse" />
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent 
        className="w-80 p-3" 
        align="start"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="space-y-3">
          <div className="font-medium text-sm flex items-center gap-2">
            <StickyNote className="h-4 w-4" />
            Заметки ({notes.length})
          </div>

          {/* Список заметок */}
          {notes.length > 0 && (
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {notes.map((note) => {
                const colorConfig = getColorConfig(note.color);
                return (
                  <div
                    key={note.id}
                    className={cn(
                      'p-2 rounded-md text-sm relative group',
                      colorConfig.bg
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <p 
                          className="whitespace-pre-wrap cursor-pointer hover:underline"
                          onClick={() => startEdit(note)}
                        >
                          {note.content}
                        </p>
                        <div className="flex items-center gap-1 mt-1 text-[10px] text-muted-foreground">
                          <Calendar className="h-2.5 w-2.5" />
                          {format(new Date(note.created_at), 'd MMM yyyy, HH:mm', { locale: ru })}
                        </div>
                      </div>
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-5 w-5"
                          onClick={() => handleTogglePin(note)}
                        >
                          {note.is_pinned ? (
                            <PinOff className="h-3 w-3" />
                          ) : (
                            <Pin className="h-3 w-3" />
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-5 w-5 text-destructive hover:text-destructive"
                          onClick={() => handleDelete(note.id)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                    {note.is_pinned && (
                      <Pin className="absolute top-1 right-1 h-3 w-3 text-muted-foreground" />
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Форма создания/редактирования */}
          <div className="space-y-2 pt-2 border-t">
            <Textarea
              placeholder={editingNote ? 'Редактировать заметку...' : 'Новая заметка...'}
              value={newNoteText}
              onChange={(e) => setNewNoteText(e.target.value)}
              className="min-h-[60px] text-sm resize-none"
            />
            <div className="flex items-center justify-between">
              {/* Выбор цвета */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" className="h-7 gap-1.5">
                    <div className={cn('h-3 w-3 rounded-full', getColorConfig(newNoteColor).dot)} />
                    <span className="text-xs">Цвет</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start">
                  {NOTE_COLORS.map((color) => (
                    <DropdownMenuItem
                      key={color.value}
                      onClick={() => setNewNoteColor(color.value)}
                      className="gap-2"
                    >
                      <div className={cn('h-3 w-3 rounded-full', color.dot)} />
                      {color.label}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>

              <div className="flex gap-1">
                {editingNote && (
                  <Button variant="ghost" size="sm" className="h-7" onClick={cancelEdit}>
                    Отмена
                  </Button>
                )}
                <Button 
                  size="sm" 
                  className="h-7"
                  onClick={editingNote ? handleUpdate : handleCreate}
                  disabled={!newNoteText.trim()}
                >
                  <Plus className="h-3 w-3 mr-1" />
                  {editingNote ? 'Сохранить' : 'Добавить'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
