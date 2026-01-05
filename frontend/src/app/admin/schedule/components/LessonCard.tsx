'use client';

import { Users, MoreHorizontal, XCircle, Clock, BookOpen, RotateCcw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { LESSON_TYPE_CONFIG } from '@/lib/schedule-constants';
import { NoteButton } from '@/components/notes';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';

export interface LessonData {
  id: string;
  date: string;
  lesson_number: number;
  lesson_type: string;
  topic: string | null;
  subject_name: string | null;
  work_number: number | null;
  subgroup: number | null;
  is_cancelled: boolean;
  ended_early?: boolean;
  group_id?: string;
  group_name?: string | null;
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
        'relative rounded-md border-l-4 p-2.5 transition-all cursor-pointer',
        'hover:shadow-lg hover:scale-[1.02]',
        'border border-transparent',
        isCancelled && 'bg-red-100 dark:bg-red-900/40 border-l-red-500 opacity-70',
        isEndedEarly && !isCancelled && 'bg-yellow-100 dark:bg-yellow-900/40 border-l-yellow-500',
        !isCancelled && !isEndedEarly && `${config.bg} ${config.border}`
      )}
      onClick={onClick}
    >
      {/* Header: группа + меню */}
      <div className="flex items-start justify-between gap-1">
        <span className={cn(
          'font-bold text-sm truncate flex-1',
          isCancelled && 'line-through text-red-700 dark:text-red-300',
          isEndedEarly && !isCancelled && 'text-yellow-800 dark:text-yellow-200',
          !isCancelled && !isEndedEarly && config.text
        )}>
          {lesson.group_name || 'Группа'}
        </span>
        
        <div className="flex items-center gap-0.5 -mr-1 -mt-0.5">
          <NoteButton entityType="lesson" entityId={lesson.id} size="sm" />
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
      <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
        <span className={cn(
          'text-[10px] font-semibold px-2 py-0.5 rounded',
          isCancelled && 'bg-red-500 text-white',
          isEndedEarly && !isCancelled && 'bg-yellow-500 text-white',
          !isCancelled && !isEndedEarly && config.badge
        )}>
          {isCancelled ? 'Отменено' : isEndedEarly ? 'Отпустил' : config.label}
        </span>
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

      {/* Номер работы */}
      {lesson.work_number && !isCancelled && (
        <p className={cn(
          'text-[11px] font-semibold mt-1',
          isEndedEarly ? 'text-yellow-700 dark:text-yellow-300' : config.text
        )}>
          Работа №{lesson.work_number}
        </p>
      )}
    </div>
  );
}
