'use client';

import { useEffect, useState, useMemo } from 'react';
import { toast } from 'sonner';
import { StudentAPI, StudentAttendance, AttendanceRecord } from '@/lib/api';
import { CardSpotlight } from '@/components/ui/card-spotlight';
import { NumberTicker } from '@/components/ui/number-ticker';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { IconCheck, IconClock, IconX, IconAlertCircle, IconChevronLeft, IconChevronRight, IconCalendar, IconBook, IconFlask, IconSchool } from '@tabler/icons-react';
import { motion } from 'motion/react';
import { cn } from '@/lib/utils';

type AttendanceStatus = 'PRESENT' | 'LATE' | 'EXCUSED' | 'ABSENT';

const WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
const MONTHS = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];

const STATUS_COLORS: Record<AttendanceStatus, string> = {
  PRESENT: 'bg-green-500 text-white',
  LATE: 'bg-yellow-500 text-white',
  EXCUSED: 'bg-blue-500 text-white',
  ABSENT: 'bg-red-500 text-white',
};

const STATUS_LABELS: Record<AttendanceStatus, string> = {
  PRESENT: 'Присутствовал',
  LATE: 'Опоздание',
  EXCUSED: 'Уваж. причина',
  ABSENT: 'Пропуск',
};

const LESSON_TYPE_LABELS: Record<string, { label: string; icon: typeof IconBook }> = {
  lecture: { label: 'Лекция', icon: IconBook },
  practice: { label: 'Практика', icon: IconSchool },
  lab: { label: 'Лаба', icon: IconFlask },
};

export default function AttendancePage() {
  const [loading, setLoading] = useState(true);
  const [attendance, setAttendance] = useState<StudentAttendance | null>(null);
  const [currentDate, setCurrentDate] = useState(new Date());

  useEffect(() => {
    const loadAttendance = async () => {
      try {
        const data = await StudentAPI.getAttendance();
        setAttendance(data);
      } catch {
        toast.error('Ошибка загрузки посещаемости');
      } finally {
        setLoading(false);
      }
    };
    loadAttendance();
  }, []);

  // Build attendance map from records
  const attendanceMap = useMemo(() => {
    const map: Record<string, AttendanceStatus> = {};
    if (attendance?.records) {
      attendance.records.forEach((r) => {
        // Берём первый статус за день (или можно агрегировать)
        if (!map[r.date]) {
          map[r.date] = r.status as AttendanceStatus;
        }
      });
    }
    return map;
  }, [attendance]);

  // Calendar days generation (compact 5 weeks)
  const calendarDays = useMemo(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();

    let startDay = firstDay.getDay() - 1;
    if (startDay === -1) startDay = 6;

    const days: { date: number; isCurrentMonth: boolean; dateStr?: string; isToday?: boolean }[] = [];
    const today = new Date();
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

    const prevMonth = new Date(year, month, 0);
    const prevMonthDays = prevMonth.getDate();
    for (let i = startDay - 1; i >= 0; i--) {
      days.push({ date: prevMonthDays - i, isCurrentMonth: false });
    }

    for (let i = 1; i <= daysInMonth; i++) {
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;
      days.push({ date: i, isCurrentMonth: true, dateStr, isToday: dateStr === todayStr });
    }

    const remaining = 35 - days.length; // 5 weeks
    for (let i = 1; i <= remaining; i++) {
      days.push({ date: i, isCurrentMonth: false });
    }

    return days;
  }, [currentDate]);

  // Group records by date for the list
  const recordsByDate = useMemo(() => {
    if (!attendance?.records) return [];
    
    const grouped: Record<string, AttendanceRecord[]> = {};
    attendance.records.forEach((r) => {
      if (!grouped[r.date]) grouped[r.date] = [];
      grouped[r.date].push(r);
    });
    
    return Object.entries(grouped)
      .sort(([a], [b]) => b.localeCompare(a))
      .slice(0, 20); // Last 20 days
  }, [attendance]);

  const goToPrevMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  const goToNextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  if (loading) return <AttendanceSkeleton />;

  if (!attendance) {
    return (
      <div className="p-6 max-w-6xl mx-auto">
        <CardSpotlight className="p-12 text-center">
          <IconAlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">Нет данных</h3>
          <p className="text-muted-foreground">Данные о посещаемости появятся здесь после первого занятия</p>
        </CardSpotlight>
      </div>
    );
  }

  const { stats } = attendance;

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-2xl font-bold text-foreground">Посещаемость</h1>
        <p className="text-muted-foreground">Всего занятий: {stats.total_classes}</p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <CardSpotlight className="p-4 text-center">
          <p className="text-3xl font-bold text-green-500">
            <NumberTicker value={Math.round(stats.attendance_rate)} />%
          </p>
          <p className="text-xs text-muted-foreground">Посещаемость</p>
        </CardSpotlight>
        <StatMini icon={<IconCheck className="h-4 w-4" />} label="Был" value={stats.present} color="green" />
        <StatMini icon={<IconClock className="h-4 w-4" />} label="Опоздал" value={stats.late} color="yellow" />
        <StatMini icon={<IconAlertCircle className="h-4 w-4" />} label="Уваж." value={stats.excused} color="blue" />
        <StatMini icon={<IconX className="h-4 w-4" />} label="Пропуск" value={stats.absent} color="red" />
      </div>

      {/* Main Grid: Calendar + Records List */}
      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        {/* Compact Calendar */}
        <CardSpotlight className="p-4">
          <div className="flex items-center justify-between mb-3">
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={goToPrevMonth}>
              <IconChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-sm font-medium">
              {MONTHS[currentDate.getMonth()]} {currentDate.getFullYear()}
            </span>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={goToNextMonth}>
              <IconChevronRight className="h-4 w-4" />
            </Button>
          </div>

          {/* Weekday headers */}
          <div className="grid grid-cols-7 gap-1 mb-1">
            {WEEKDAYS.map((day) => (
              <div key={day} className="py-1 text-center text-[10px] font-medium text-muted-foreground">
                {day}
              </div>
            ))}
          </div>

          {/* Calendar grid - compact */}
          <div className="grid grid-cols-7 gap-1">
            {calendarDays.map((day, idx) => {
              const status = day.dateStr ? attendanceMap[day.dateStr] : undefined;
              return (
                <div
                  key={idx}
                  className={cn(
                    "aspect-square rounded-md flex items-center justify-center text-xs transition-all",
                    !day.isCurrentMonth && "text-muted-foreground/30",
                    day.isCurrentMonth && !status && "text-foreground hover:bg-accent/50",
                    day.isToday && "ring-2 ring-primary ring-offset-1 ring-offset-background",
                    status && STATUS_COLORS[status]
                  )}
                  title={status ? STATUS_LABELS[status] : undefined}
                >
                  {day.date}
                </div>
              );
            })}
          </div>

          {/* Legend */}
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

        {/* Records List */}
        <CardSpotlight className="p-4">
          <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
            <IconCalendar className="h-4 w-4 text-primary" />
            История посещений
          </h3>
          
          {recordsByDate.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">Нет записей</p>
          ) : (
            <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2">
              {recordsByDate.map(([date, records]) => (
                <div key={date} className="border border-border rounded-lg p-3">
                  <div className="text-xs font-medium text-muted-foreground mb-2">
                    {formatDate(date)}
                  </div>
                  <div className="space-y-1.5">
                    {records.map((r, idx) => {
                      const status = r.status as AttendanceStatus;
                      const lessonType = r.lesson_type ? LESSON_TYPE_LABELS[r.lesson_type] : null;
                      const LessonIcon = lessonType?.icon || IconBook;
                      
                      return (
                        <div key={idx} className="flex items-center gap-2 text-sm">
                          <div className={cn(
                            "h-2 w-2 rounded-full shrink-0",
                            status === 'PRESENT' && "bg-green-500",
                            status === 'LATE' && "bg-yellow-500",
                            status === 'EXCUSED' && "bg-blue-500",
                            status === 'ABSENT' && "bg-red-500"
                          )} />
                          {r.lesson_number && (
                            <span className="text-xs text-muted-foreground w-12">{r.lesson_number} пара</span>
                          )}
                          {lessonType && (
                            <span className="flex items-center gap-1 text-xs text-muted-foreground">
                              <LessonIcon className="h-3 w-3" />
                              {lessonType.label}
                            </span>
                          )}
                          <span className={cn(
                            "ml-auto text-xs font-medium",
                            status === 'PRESENT' && "text-green-500",
                            status === 'LATE' && "text-yellow-500",
                            status === 'EXCUSED' && "text-blue-500",
                            status === 'ABSENT' && "text-red-500"
                          )}>
                            {STATUS_LABELS[status]}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardSpotlight>
      </div>
    </div>
  );
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  const day = date.getDate();
  const month = MONTHS[date.getMonth()];
  const weekday = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'][date.getDay()];
  return `${weekday}, ${day} ${month.toLowerCase().slice(0, 3)}`;
}

function StatMini({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: number; color: 'green' | 'yellow' | 'blue' | 'red' }) {
  const colorClasses = {
    green: 'text-green-500',
    yellow: 'text-yellow-500',
    blue: 'text-blue-500',
    red: 'text-red-500',
  };

  return (
    <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="p-3 rounded-xl border border-border bg-card flex items-center gap-2">
      <span className={colorClasses[color]}>{icon}</span>
      <div>
        <p className="text-lg font-bold text-foreground">{value}</p>
        <p className="text-[10px] text-muted-foreground">{label}</p>
      </div>
    </motion.div>
  );
}

function AttendanceSkeleton() {
  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div className="space-y-2"><Skeleton className="h-8 w-48" /><Skeleton className="h-4 w-32" /></div>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-20 rounded-xl" />)}
      </div>
      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <Skeleton className="h-[350px] rounded-xl" />
        <Skeleton className="h-[350px] rounded-xl" />
      </div>
    </div>
  );
}
