'use client';

import { useMemo } from 'react';
import { format, addDays, startOfWeek, isToday, isPast } from 'date-fns';
import { ru } from 'date-fns/locale';
import { cn } from '@/lib/utils';
import { LESSON_TIMES, WEEKDAYS } from '@/lib/schedule-constants';
import { LessonCard, LessonData } from './LessonCard';
import { LectureCard } from './LectureCard';
import type { GroupedLecture } from '@/components/schedule';

interface ScheduleGridProps {
  lessons: LessonData[];
  groupedLectures?: GroupedLecture[];
  currentWeek: Date;
  onLessonClick?: (lesson: LessonData) => void;
  onLectureClick?: (lecture: GroupedLecture) => void;
  onLessonAction?: (lessonId: string, action: 'cancel' | 'end_early' | 'restore') => void;
}

const SCHEDULE_GRID_TEMPLATE = 'grid-cols-[72px_repeat(6,minmax(0,1fr))]';

export function ScheduleGrid({ lessons, groupedLectures = [], currentWeek, onLessonClick, onLectureClick, onLessonAction }: ScheduleGridProps) {
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

  // Группируем лекции по date-lesson_number
  const lecturesBySlot = useMemo(() => {
    const map = new Map<string, GroupedLecture[]>();
    groupedLectures.forEach((lecture) => {
      const key = `${lecture.date}-${lecture.lesson_number}`;
      if (!map.has(key)) {
        map.set(key, []);
      }
      map.get(key)!.push(lecture);
    });
    return map;
  }, [groupedLectures]);

  // Находим активные слоты (где есть занятия)
  const activeSlots = useMemo(() => {
    const slots = new Set<number>();
    lessons.forEach((lesson) => slots.add(lesson.lesson_number));
    groupedLectures.forEach((lecture) => slots.add(lecture.lesson_number));
    return Array.from(slots).sort((a, b) => a - b);
  }, [lessons, groupedLectures]);

  // Если нет занятий — показываем слоты 1-4
  const slotsToShow = activeSlots.length > 0 ? activeSlots : [1, 2, 3, 4];

  return (
    <div className="w-full overflow-x-auto rounded-lg border border-zinc-300 dark:border-zinc-700 bg-card shadow-sm">
      <div className="min-w-[700px]">
        {/* Header: дни недели */}
        <div className={cn('grid border-b border-zinc-300 dark:border-zinc-700', SCHEDULE_GRID_TEMPLATE)}>
          <div className="p-3 text-xs font-medium text-muted-foreground text-center border-r border-zinc-300 dark:border-zinc-700">
            Пара
          </div>
          {weekDates.map((date, index) => {
            const today = isToday(date);
            const past = isPast(date) && !today;

            return (
              <div
                key={index}
                className={cn(
                  'min-w-0 p-3 text-center border-r border-zinc-300 dark:border-zinc-700 last:border-r-0',
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
                'grid',
                SCHEDULE_GRID_TEMPLATE,
                slotIndex < slotsToShow.length - 1 && 'border-b border-zinc-300 dark:border-zinc-700'
              )}
            >
              {/* Колонка времени */}
              <div className="p-2 flex flex-col justify-center items-center border-r border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-muted/30">
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
                const cellLectures = lecturesBySlot.get(key) || [];
                const today = isToday(date);
                const past = isPast(date) && !today;
                const hasContent = cellLessons.length > 0 || cellLectures.length > 0;

                return (
                  <div
                    key={dayIndex}
                    className={cn(
                      'min-h-[100px] min-w-0 p-1.5 border-r border-zinc-300 dark:border-zinc-700 last:border-r-0',
                      today && 'bg-primary/5 dark:bg-primary/10',
                      past && 'bg-zinc-50 dark:bg-muted/30',
                      !hasContent && 'group'
                    )}
                  >
                    {hasContent ? (
                      <div className="flex min-w-0 flex-col gap-1 items-stretch">
                        {/* Grouped lectures */}
                        {cellLectures.map((lecture, idx) => (
                          <LectureCard
                            key={`lecture-${idx}`}
                            lecture={lecture}
                            onClick={() => onLectureClick?.(lecture)}
                          />
                        ))}
                        {/* Regular lessons (labs, practices) */}
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
