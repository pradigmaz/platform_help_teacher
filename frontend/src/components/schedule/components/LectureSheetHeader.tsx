'use client';

import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { X, Calendar, BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import type { GroupedLecture } from '../types';
import { LESSON_TIMES } from '../constants';

interface LectureSheetHeaderProps {
  lecture: GroupedLecture;
  topic: string;
  onClose: () => void;
  onTopicChange: (topic: string) => void;
}

function formatGroupsRange(groups: { name: string }[]): string {
  if (groups.length === 0) return '';
  if (groups.length === 1) return groups[0].name;
  
  // Extract 3-digit group numbers (e.g., ИС1-236-ОТ → 236)
  const numbers = groups
    .map(g => {
      const match = g.name.match(/(\d{3})/);  // Match 3-digit number
      return match ? parseInt(match[1]) : 0;
    })
    .filter(n => n > 0)
    .sort((a, b) => a - b);
  
  if (numbers.length === 0) return groups.map(g => g.name).join(', ');
  
  // Check if consecutive
  const isConsecutive = numbers.every((n, i) => i === 0 || n === numbers[i - 1] + 1);
  
  if (isConsecutive && numbers.length > 2) {
    return `${numbers[0]}-${numbers[numbers.length - 1]}`;
  }
  
  return numbers.join(', ');
}

export function LectureSheetHeader({
  lecture,
  topic,
  onClose,
  onTopicChange,
}: LectureSheetHeaderProps) {
  const timeSlot = LESSON_TIMES[lecture.lesson_number - 1] || '';
  const groupsDisplay = formatGroupsRange(lecture.groups);

  return (
    <div className="flex-none p-5 border-b bg-muted/30">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2 text-muted-foreground text-xs">
          <Calendar className="h-3 w-3" />
          <span>{format(new Date(lecture.date), 'EEEE, d MMMM', { locale: ru })}</span>
          <span>•</span>
          <span>{lecture.lesson_number} пара ({timeSlot})</span>
        </div>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>
      
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-2xl font-bold">{groupsDisplay}</h2>
        <Badge className="bg-blue-500/15 text-blue-400 border-blue-500/20 border">
          Лекция
        </Badge>
      </div>
      
      <div className="space-y-1">
        <div className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
          Предмет
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <BookOpen className="h-4 w-4" />
          {lecture.subject_name || 'Предмет'}
        </div>
      </div>
      
      <div className="mt-2 space-y-1">
        <div className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
          Тема
        </div>
        <Input
          value={topic}
          onChange={(event) => onTopicChange(event.target.value)}
          placeholder="Введите тему лекции..."
          className="h-9"
        />
      </div>
    </div>
  );
}
