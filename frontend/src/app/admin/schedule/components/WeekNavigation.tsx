'use client';

import { format, startOfWeek, addDays, addWeeks, subWeeks, startOfToday, getDay } from 'date-fns';
import { ru } from 'date-fns/locale';
import { ChevronLeft, ChevronRight, CalendarIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';

interface WeekNavigationProps {
  currentWeek: Date;
  onWeekChange: (date: Date) => void;
}

export function WeekNavigation({ currentWeek, onWeekChange }: WeekNavigationProps) {
  const weekStart = startOfWeek(currentWeek, { weekStartsOn: 1 });
  // Показываем Пн-Сб (5 дней от понедельника = суббота)
  const weekEnd = addDays(weekStart, 5);

  return (
    <div className="flex items-center gap-2">
      <Button 
        variant="outline" 
        size="icon" 
        onClick={() => onWeekChange(subWeeks(currentWeek, 1))}
      >
        <ChevronLeft className="w-4 h-4" />
      </Button>
      
      <Button
        variant="outline"
        onClick={() => {
          const today = startOfToday();
          // Если воскресенье — показываем следующую неделю
          if (getDay(today) === 0) {
            onWeekChange(addWeeks(today, 1));
          } else {
            onWeekChange(today);
          }
        }}
      >
        Сегодня
      </Button>
      
      <Popover>
        <PopoverTrigger asChild>
          <Button variant="outline" className="min-w-[200px] justify-center gap-2">
            <CalendarIcon className="w-4 h-4" />
            {format(weekStart, 'd MMM', { locale: ru })} — {format(weekEnd, 'd MMM', { locale: ru })}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="center">
          <Calendar
            mode="single"
            selected={currentWeek}
            onSelect={(date) => date && onWeekChange(date)}
            locale={ru}
            weekStartsOn={1}
            captionLayout="dropdown-months"
          />
        </PopoverContent>
      </Popover>
      <Button 
        variant="outline" 
        size="icon" 
        onClick={() => onWeekChange(addWeeks(currentWeek, 1))}
      >
        <ChevronRight className="w-4 h-4" />
      </Button>
    </div>
  );
}
