'use client';

import { useMemo } from 'react';
import { format, addDays, startOfWeek, isToday, isPast } from 'date-fns';
import { ru } from 'date-fns/locale';
import { cn } from '@/lib/utils';
import { LESSON_TIMES, WEEKDAYS } from '@/lib/schedule-constants';
import { LessonCard, LessonData } from './LessonCard';

interface ScheduleGridProps {
  lessons: LessonData[];
  currentWeek: Date;
  onLessonClick?: (lesson: LessonData) => void;
  onLessonAction?: (lessonId: string, action: 'cancel' | 'end_early' | 'restore') => void;
}

export function ScheduleGrid({ lessons, currentWeek, onLessonClick, onLessonAction }: ScheduleGridProps) {
  const weekStart = startOfWeek(currentWeek, { weekStartsOn: 1 });
  
  // Генерируем даты недели (Пн-Сб)
  const weekDates = useMemo(() => {
    return Array.from({ length: 6 }, (_, i) => addDays(weekStart, i));
  }, [weekStart]);

  // Группируем занятия по date-lesson_number
  const lessonsBySlot = useMemo(() => {
    const map = new Map<string, LessonData[]>();
    lessons.forEach((lesson) => {
      const key = `${lesson.date}-${lesson.lesson_number}`;
      if (!map.has(key)) {
        map.set(key, []);
      }
      map.get(key)!.push(lesson);
    });
    return map;
  }, [lessons]);

  // Находим активные слоты (где есть занятия)
  const activeSlots = useMemo(() => {
    const slots = new Set<number>();
    lessons.forEach((lesson) => slots.add(lesson.lesson_number));
    return Array.from(slots).sort((a, b) => a - b);
  }, [lessons]);

  // Если нет занятий — показываем слоты 1-4
  const slotsToShow = activeSlots.length > 0 ? activeSlots : [1, 2, 3, 4];

  return (
    <div className="overflow-x-auto rounded-lg border border-border bg-card shadow-sm">
      <div className="min-w-[700px]">
        {/* Header: дни недели */}
        <div className="grid grid-cols-[80px_repeat(6,1fr)] border-b border-border">
          <div className="p-3 text-xs font-medium text-muted-foreground text-center border-r border-border">
            Пара
          </div>
          {weekDates.map((date, index) => {
            const today = isToday(date);
            const past = isPast(date) && !today;

            return (
              <div
                key={index}
                className={cn(
                  'p-3 text-center border-r border-border last:border-r-0',
                  today && 'bg-primary/10 dark:bg-primary/20',
                  past && 'opacity-50'
                )}
              >
                <div className={cn(
                  'text-xs font-medium',
                  today ? 'text-primary' : 'text-muted-foreground'
                )}>
                  {WEEKDAYS[index].label}
                </div>
                <div className={cn(
                  'text-lg font-bold',
                  today ? 'text-primary' : past ? 'text-muted-foreground' : 'text-foreground'
                )}>
                  {format(date, 'd', { locale: ru })}
                </div>
              </div>
            );
          })}
        </div>

        {/* Body: слоты пар */}
        <div>
          {slotsToShow.map((slotNumber, slotIndex) => (
            <div 
              key={slotNumber} 
              className={cn(
                'grid grid-cols-[80px_repeat(6,1fr)]',
                slotIndex < slotsToShow.length - 1 && 'border-b border-border'
              )}
            >
              {/* Колонка времени */}
              <div className="p-2 flex flex-col justify-center items-center border-r border-border bg-muted/30">
                <span className="text-lg font-bold text-muted-foreground">
                  {slotNumber}
                </span>
                <span className="text-[10px] text-muted-foreground">
                  {LESSON_TIMES[slotNumber]?.start}
                </span>
                <span className="text-[10px] text-muted-foreground">
                  {LESSON_TIMES[slotNumber]?.end}
                </span>
              </div>

              {/* Ячейки дней */}
              {weekDates.map((date, dayIndex) => {
                const dateStr = format(date, 'yyyy-MM-dd');
                const key = `${dateStr}-${slotNumber}`;
                const cellLessons = lessonsBySlot.get(key) || [];
                const today = isToday(date);
                const past = isPast(date) && !today;

                return (
                  <div
                    key={dayIndex}
                    className={cn(
                      'min-h-[100px] p-1.5 border-r border-border last:border-r-0',
                      today && 'bg-primary/5 dark:bg-primary/10',
                      past && 'bg-muted/30',
                      cellLessons.length === 0 && 'group'
                    )}
                  >
                    {cellLessons.length > 0 ? (
                      <div className="space-y-1">
                        {cellLessons.map((lesson) => (
                          <LessonCard
                            key={lesson.id}
                            lesson={lesson}
                            onClick={() => onLessonClick?.(lesson)}
                            onAction={(action) => onLessonAction?.(lesson.id, action)}
                          />
                        ))}
                      </div>
                    ) : (
                      <div className="h-full w-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                        <div className="w-full h-full border-2 border-dashed border-border rounded-md" />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
