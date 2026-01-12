'use client';

import { BookOpen } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { NoteButton } from '@/components/notes';
import type { LessonData } from '../types';
import { canHaveGrade } from '../constants';

interface LessonTopicProps {
  lesson: LessonData;
  topic: string;
  workNumber?: number | null;
  onChange: (topic: string) => void;
  onWorkNumberChange?: (workNumber: number | null) => void;
}

export function LessonTopic({ lesson, topic, workNumber, onChange, onWorkNumberChange }: LessonTopicProps) {
  const showWorkNumberSelect = canHaveGrade(lesson.lesson_type) && lesson.lesson_type.toLowerCase() === 'lab';
  const currentWorkNumber = workNumber ?? lesson.work_number;

  return (
    <div className="space-y-3">
      <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
        Тема занятия
      </Label>
      <div className="flex items-center gap-2 text-sm text-muted-foreground px-3 py-2 bg-muted rounded-md">
        <BookOpen className="h-4 w-4" />
        {lesson.subject_name || 'Предмет'}
      </div>
      
      {showWorkNumberSelect && onWorkNumberChange && (
        <div className="space-y-1.5">
          <Label className="text-xs text-muted-foreground">Номер лабораторной работы</Label>
          <Select
            value={currentWorkNumber?.toString() || ''}
            onValueChange={(v) => onWorkNumberChange(v ? parseInt(v) : null)}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Выберите номер лабы..." />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">Не указано</SelectItem>
              {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
                <SelectItem key={n} value={n.toString()}>
                  Лабораторная работа №{n}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}
      
      <div className="relative">
        <Input
          value={topic}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Введите тему занятия..."
          className={currentWorkNumber ? "pr-16" : ""}
        />
        {currentWorkNumber && (
          <div className="absolute right-2 top-1/2 -translate-y-1/2 bg-muted text-muted-foreground text-[10px] px-1.5 py-0.5 rounded">
            ЛР №{currentWorkNumber}
          </div>
        )}
      </div>
      <div className="flex justify-end">
        <NoteButton entityType="lesson" entityId={lesson.id} size="md" />
      </div>
    </div>
  );
}
