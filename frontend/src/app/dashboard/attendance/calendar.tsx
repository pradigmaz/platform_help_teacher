import { IconChevronLeft, IconChevronRight } from '@tabler/icons-react';
import { Button } from '@/components/ui/button';
import { CardSpotlight } from '@/components/ui/card-spotlight';
import { cn } from '@/lib/utils';
import type { AttendanceMap, CalendarDay } from './types';
import { MONTHS, STATUS_COLORS, STATUS_LABELS, WEEKDAYS } from './types';

type CompactCalendarProps = {
  currentDate: Date;
  calendarDays: CalendarDay[];
  attendanceMap: AttendanceMap;
  onPrev: () => void;
  onNext: () => void;
};

export function CompactCalendar({ currentDate, calendarDays, attendanceMap, onPrev, onNext }: CompactCalendarProps) {
  return (
    <CardSpotlight className="p-4">
      <div className="flex items-center justify-between mb-3">
        <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onPrev} aria-label="Предыдущий месяц">
          <IconChevronLeft className="h-4 w-4" />
        </Button>
        <span className="text-sm font-medium" aria-live="polite">
          {MONTHS[currentDate.getMonth()]} {currentDate.getFullYear()}
        </span>
        <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onNext} aria-label="Следующий месяц">
          <IconChevronRight className="h-4 w-4" />
        </Button>
      </div>

      <div className="grid grid-cols-7 gap-1 mb-1">
        {WEEKDAYS.map((day) => (
          <div key={day} className="py-1 text-center text-[10px] font-medium text-muted-foreground">
            {day}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-7 gap-1">
        {calendarDays.map((day, idx) => {
          const status = day.dateStr ? attendanceMap[day.dateStr] : undefined;
          return (
            <div
              key={`${day.date}-${idx}`}
              className={cn(
                'aspect-square rounded-md flex items-center justify-center text-xs transition-all',
                !day.isCurrentMonth && 'text-muted-foreground/30',
                day.isCurrentMonth && !status && 'text-foreground hover:bg-accent/50',
                day.isToday && 'ring-2 ring-primary ring-offset-1 ring-offset-background',
                status && STATUS_COLORS[status]
              )}
              title={status ? STATUS_LABELS[status] : undefined}
            >
              {day.date}
            </div>
          );
        })}
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2 border-t border-border pt-3">
        <div className="flex items-center gap-1.5">
          <div className="h-2.5 w-2.5 rounded bg-green-500" />
          <span className="text-[10px] text-muted-foreground">Был</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="h-2.5 w-2.5 rounded bg-yellow-500" />
          <span className="text-[10px] text-muted-foreground">Опоздал</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="h-2.5 w-2.5 rounded bg-blue-500" />
          <span className="text-[10px] text-muted-foreground">Уваж.</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="h-2.5 w-2.5 rounded bg-red-500" />
          <span className="text-[10px] text-muted-foreground">Пропуск</span>
        </div>
      </div>
    </CardSpotlight>
  );
}
