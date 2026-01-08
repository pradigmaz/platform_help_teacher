'use client';

import { BookOpen } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { NoteButton } from '@/components/notes';
import type { LessonData } from '../types';
import { canHaveGrade } from '../constants';

interface LessonTopicProps {
  lesson: LessonData;
  topic: string;
  onChange: (topic: string) => void;
}

export function LessonTopic({ lesson, topic, onChange }: LessonTopicProps) {
  const showWorkNumber = canHaveGrade(lesson.lesson_type) && lesson.work_number;

  return (
    <div className="space-y-2">
      <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
        Тема занятия
      </Label>
      <div className="flex items-center gap-2 text-sm text-muted-foreground px-3 py-2 bg-muted rounded-md">
        <BookOpen className="h-4 w-4" />
        {lesson.subject_name || 'Предмет'}
      </div>
      <div className="relative">
        <Input
          value={topic}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Введите тему занятия..."
          className="pr-16"
        />
        {showWorkNumber && (
          <div className="absolute right-2 top-1/2 -translate-y-1/2 bg-muted text-muted-foreground text-[10px] px-1.5 py-0.5 rounded">
            ЛР №{lesson.work_number}
          </div>
        )}
      </div>
      <div className="flex justify-end">
        <NoteButton entityType="lesson" entityId={lesson.id} size="md" />
      </div>
    </div>
  );
}
