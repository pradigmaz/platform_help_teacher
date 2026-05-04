'use client';

import { Users, MoreHorizontal, XCircle, Clock, BookOpen, RotateCcw, MapPin } from 'lucide-react';
import type { LessonAttendanceSummaryResponse } from '@/lib/api/types/schedule';
import { cn } from '@/lib/utils';
import { LESSON_TYPE_CONFIG } from '@/lib/schedule-constants';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { ScheduleAttendanceBadge } from './ScheduleAttendanceBadge';

export interface LessonData {
  id: string;
  date: string;
  lesson_number: number;
  lesson_type: string;
  topic: string | null;
  room?: string | null;
  subject_id?: string | null;
  offering_id?: string | null;
  subject_name: string | null;
  work_number: number | null;
  subgroup: number | null;
  is_cancelled: boolean;
  ended_early?: boolean;
  group_id?: string;
  group_name?: string | null;
  summary?: LessonAttendanceSummaryResponse | null;
}

interface LessonCardProps {
  lesson: LessonData;
  onClick?: () => void;
  onAction?: (action: 'cancel' | 'end_early' | 'restore') => void;
}

export function LessonCard({ lesson, onClick, onAction }: LessonCardProps) {
  const config = LESSON_TYPE_CONFIG[lesson.lesson_type as keyof typeof LESSON_TYPE_CONFIG] 
    || LESSON_TYPE_CONFIG.lecture;

  const isCancelled = lesson.is_cancelled;
  const isEndedEarly = lesson.ended_early;

  return (
    <div
      className={cn(
        'relative min-w-0 rounded-md border-l-4 p-2.5 transition-all cursor-pointer',
        'hover:shadow-lg hover:scale-[1.02]',
        'border border-transparent',
        isCancelled && 'bg-red-100 dark:bg-red-900/40 border-l-red-500 opacity-70',
        isEndedEarly && !isCancelled && 'bg-yellow-100 dark:bg-yellow-900/40 border-l-yellow-500',
        !isCancelled && !isEndedEarly && `${config.bg} ${config.border}`
      )}
      onClick={onClick}
    >
      {/* Header: группа + меню */}
      <div className="flex min-w-0 items-start justify-between gap-1">
        <span className={cn(
          'font-bold text-sm truncate flex-1',
          isCancelled && 'line-through text-red-700 dark:text-red-300',
          isEndedEarly && !isCancelled && 'text-yellow-800 dark:text-yellow-200',
          !isCancelled && !isEndedEarly && config.text
        )}>
          {lesson.group_name || 'Группа'}
        </span>
        
        <div className="flex items-center gap-0.5 -mr-1 -mt-0.5">
          <DropdownMenu>
          <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
            <Button variant="ghost" size="icon" className="h-6 w-6 hover:bg-black/10 dark:hover:bg-white/10">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" onClick={(e) => e.stopPropagation()}>
            {!isCancelled && !isEndedEarly && (
              <>
                <DropdownMenuItem onClick={() => onAction?.('cancel')}>
                  <XCircle className="mr-2 h-4 w-4 text-red-500" />
                  Отменить занятие
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onAction?.('end_early')}>
                  <Clock className="mr-2 h-4 w-4 text-yellow-500" />
                  Отпустил раньше
                </DropdownMenuItem>
              </>
            )}
            {(isCancelled || isEndedEarly) && (
              <DropdownMenuItem onClick={() => onAction?.('restore')}>
                <RotateCcw className="mr-2 h-4 w-4" />
                Восстановить
              </DropdownMenuItem>
            )}
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={onClick}>
              <BookOpen className="mr-2 h-4 w-4" />
              Открыть журнал
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        </div>
      </div>

      {/* Тип + подгруппа */}
      <div className="mt-1.5 flex min-w-0 flex-wrap items-center gap-1.5">
        <span className={cn(
          'text-[10px] font-semibold px-2 py-0.5 rounded',
          isCancelled && 'bg-red-500 text-white',
          isEndedEarly && !isCancelled && 'bg-yellow-500 text-white',
          !isCancelled && !isEndedEarly && config.badge
        )}>
          {isCancelled ? 'Отменено' : isEndedEarly ? 'Отпустил' : config.label}
        </span>
        <ScheduleAttendanceBadge summary={lesson.summary} />
        {lesson.subgroup && (
          <span className={cn(
            'text-[10px] font-medium flex items-center gap-0.5',
            isCancelled ? 'text-red-600 dark:text-red-300' : 
            isEndedEarly ? 'text-yellow-700 dark:text-yellow-300' : 
            config.text
          )}>
            <Users className="h-3 w-3" />
            {lesson.subgroup} п.г.
          </span>
        )}
        {lesson.room && (
          <span className={cn(
            'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-bold shadow-sm ring-1',
            isCancelled
              ? 'border-red-300 bg-red-100 text-red-800 ring-red-200 dark:border-red-400/40 dark:bg-red-500/15 dark:text-red-100 dark:ring-red-400/20'
              : isEndedEarly
                ? 'border-yellow-300 bg-yellow-100 text-yellow-900 ring-yellow-200 dark:border-yellow-300/40 dark:bg-yellow-400/15 dark:text-yellow-100 dark:ring-yellow-300/20'
                : 'border-amber-300 bg-amber-100 text-amber-950 ring-amber-200 dark:border-amber-300/40 dark:bg-amber-400/20 dark:text-amber-100 dark:ring-amber-300/20'
          )}>
            <MapPin className="h-3 w-3 shrink-0" />
            ауд. {lesson.room}
          </span>
        )}
      </div>

      {/* Тема/предмет */}
      <p className={cn(
        'mt-1.5 text-xs font-medium line-clamp-2',
        isCancelled ? 'text-red-600 dark:text-red-300 line-through' : 
        isEndedEarly ? 'text-yellow-700 dark:text-yellow-200' :
        config.text
      )}>
        {lesson.topic || lesson.subject_name || '—'}
      </p>
    </div>
  );
}
