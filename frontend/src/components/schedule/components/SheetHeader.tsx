'use client';

import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { X, Calendar } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type { LessonData } from '../types';
import { LESSON_TIMES, TYPE_CONFIG } from '../constants';

interface SheetHeaderProps {
  lesson: LessonData;
  onClose: () => void;
}

export function SheetHeader({ lesson, onClose }: SheetHeaderProps) {
  const typeConfig = TYPE_CONFIG[lesson.lesson_type.toLowerCase()] || TYPE_CONFIG.lecture;
  const timeSlot = LESSON_TIMES[lesson.lesson_number - 1] || '';

  return (
    <div className="flex-none p-5 border-b bg-muted/30">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2 text-muted-foreground text-xs">
          <Calendar className="h-3 w-3" />
          <span>{format(new Date(lesson.date), 'EEEE, d MMMM', { locale: ru })}</span>
          <span>•</span>
          <span>{lesson.lesson_number} пара ({timeSlot})</span>
        </div>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">{lesson.group_name || 'Группа'}</h2>
        <Badge className={cn('border', typeConfig.color)}>{typeConfig.label}</Badge>
      </div>
      {lesson.subgroup && (
        <div className="text-sm text-muted-foreground mt-1">{lesson.subgroup} подгруппа</div>
      )}
    </div>
  );
}
