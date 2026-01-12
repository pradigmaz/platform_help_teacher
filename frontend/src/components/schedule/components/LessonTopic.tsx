'use client';

import { useEffect, useState } from 'react';
import { BookOpen } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { NoteButton } from '@/components/notes';
import type { LessonData } from '../types';
import { canHaveGrade } from '../constants';
import api from '@/lib/api';

interface Lab {
  id: string;
  number: number;
  title: string;
  subject_id?: string;
}

interface LessonTopicProps {
  lesson: LessonData;
  topic: string;
  workNumber?: number | null;
  onChange: (topic: string) => void;
  onWorkNumberChange?: (workNumber: number | null) => void;
}

export function LessonTopic({ lesson, topic, workNumber, onChange, onWorkNumberChange }: LessonTopicProps) {
  const [labs, setLabs] = useState<Lab[]>([]);
  const showWorkNumberSelect = canHaveGrade(lesson.lesson_type) && lesson.lesson_type.toLowerCase() === 'lab';
  const currentWorkNumber = workNumber ?? lesson.work_number;

  // Load labs for this subject
  useEffect(() => {
    if (!showWorkNumberSelect) return;
    
    const loadLabs = async () => {
      try {
        const params: Record<string, string> = {};
        if (lesson.subject_id) {
          params.subject_id = lesson.subject_id;
        }
        const { data } = await api.get<Lab[]>('/admin/labs', { params });
        // Filter by subject if needed and sort by number
        const filtered = lesson.subject_id 
          ? data.filter(l => !l.subject_id || l.subject_id === lesson.subject_id)
          : data;
        setLabs(filtered.sort((a, b) => a.number - b.number));
      } catch {
        setLabs([]);
      }
    };
    loadLabs();
  }, [showWorkNumberSelect, lesson.subject_id]);

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
          <Label className="text-xs text-muted-foreground">Лабораторная работа</Label>
          <Select
            value={currentWorkNumber?.toString() || 'none'}
            onValueChange={(v) => onWorkNumberChange(v === 'none' ? null : parseInt(v))}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Выберите лабораторную..." />
            </SelectTrigger>
            <SelectContent className="z-[10000]">
              <SelectItem value="none">Не указано</SelectItem>
              {labs.map((lab) => (
                <SelectItem key={lab.id} value={lab.number.toString()}>
                  №{lab.number}: {lab.title}
                </SelectItem>
              ))}
              {labs.length === 0 && (
                <div className="px-2 py-1.5 text-sm text-muted-foreground">
                  Нет созданных лабораторных
                </div>
              )}
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
