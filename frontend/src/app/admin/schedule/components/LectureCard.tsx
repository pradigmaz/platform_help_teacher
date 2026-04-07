'use client';

import { Users } from 'lucide-react';
import { cn } from '@/lib/utils';
import { NoteButton } from '@/components/notes';
import type { GroupedLecture } from '@/components/schedule';
import { ScheduleAttendanceBadge } from './ScheduleAttendanceBadge';

interface LectureCardProps {
  lecture: GroupedLecture;
  onClick?: () => void;
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

export function LectureCard({ lecture, onClick }: LectureCardProps) {
  const groupsDisplay = formatGroupsRange(lecture.groups);
  const isCancelled = lecture.is_cancelled;
  const isEndedEarly = lecture.ended_early;

  return (
    <div
      onClick={onClick}
      className={cn(
        'relative min-w-0 rounded-md border-l-4 p-2.5 cursor-pointer',
        'hover:shadow-lg hover:scale-[1.02]',
        'border border-transparent',
        'transition-all duration-300 ease-in-out',
        isCancelled && 'bg-red-100 dark:bg-red-900/40 border-l-red-500 opacity-70',
        isEndedEarly && !isCancelled && 'bg-yellow-100 dark:bg-yellow-900/40 border-l-yellow-500',
        !isCancelled && !isEndedEarly && 'bg-blue-500/10 border-l-blue-500'
      )}
    >
      {/* Header: группы + заметки */}
      <div className="flex min-w-0 items-start justify-between gap-1">
        <span className={cn(
          'font-bold text-sm truncate flex-1',
          isCancelled && 'line-through text-red-700 dark:text-red-300',
          isEndedEarly && !isCancelled && 'text-yellow-800 dark:text-yellow-200',
          !isCancelled && !isEndedEarly && 'text-foreground'
        )}>
          {groupsDisplay}
        </span>
        <div className="flex items-center gap-0.5 -mr-1 -mt-0.5">
          {lecture.groups.length > 0 && (
            <NoteButton 
              entityType="lesson" 
              entityId={lecture.groups[0].lesson_id} 
              size="sm" 
            />
          )}
        </div>
      </div>

      {/* Тип + кол-во групп */}
      <div className="mt-1.5 flex min-w-0 flex-wrap items-center gap-1.5">
        <span className={cn(
          'text-[10px] font-semibold px-2 py-0.5 rounded',
          isCancelled && 'bg-red-500 text-white',
          isEndedEarly && !isCancelled && 'bg-yellow-500 text-white',
          !isCancelled && !isEndedEarly && 'bg-blue-500/20 text-blue-600 dark:text-blue-400'
        )}>
          {isCancelled ? 'Отменено' : isEndedEarly ? 'Отпустил' : 'Лекция'}
        </span>
        <ScheduleAttendanceBadge summary={lecture.summary} />
        <span className={cn(
          'text-[10px] font-medium flex items-center gap-0.5',
          isCancelled ? 'text-red-600 dark:text-red-300' : 
          isEndedEarly ? 'text-yellow-700 dark:text-yellow-300' : 
          'text-blue-600 dark:text-blue-400'
        )}>
          <Users className="h-3 w-3" />
          {lecture.groups.length} групп
        </span>
      </div>

      {/* Предмет */}
      <p className={cn(
        'mt-1.5 text-xs font-medium line-clamp-2',
        isCancelled ? 'text-red-600 dark:text-red-300 line-through' : 
        isEndedEarly ? 'text-yellow-700 dark:text-yellow-200' :
        'text-blue-600 dark:text-blue-400'
      )}>
        {lecture.subject_name || 'Предмет'}
      </p>
    </div>
  );
}
