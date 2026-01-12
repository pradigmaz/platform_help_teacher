'use client';

import { useEffect, useState, useMemo } from 'react';
import { toast } from 'sonner';
import { StudentAPI, StudentAttendance } from '@/lib/api';
import { CardSpotlight } from '@/components/ui/card-spotlight';
import { NumberTicker } from '@/components/ui/number-ticker';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { IconCheck, IconClock, IconX, IconAlertCircle, IconChevronLeft, IconChevronRight, IconCalendar } from '@tabler/icons-react';
import { motion } from 'motion/react';
import { cn } from '@/lib/utils';

type AttendanceStatus = 'present' | 'late' | 'excused' | 'absent';

const WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
const MONTHS = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];

const STATUS_COLORS: Record<AttendanceStatus, string> = {
  present: 'bg-green-500 text-white',
  late: 'bg-yellow-500 text-white',
  excused: 'bg-blue-500 text-white',
  absent: 'bg-red-500 text-white',
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
        map[r.date] = r.status.toLowerCase() as AttendanceStatus;
      });
    }
    return map;
  }, [attendance]);

  // Calendar days generation
  const calendarDays = useMemo(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();

    // Get day of week for first day (0 = Sunday, adjust for Monday start)
    let startDay = firstDay.getDay() - 1;
    if (startDay === -1) startDay = 6;

    const days: { date: number; isCurrentMonth: boolean; dateStr?: string }[] = [];

    // Padding for days before first day
    const prevMonth = new Date(year, month, 0);
    const prevMonthDays = prevMonth.getDate();
    for (let i = startDay - 1; i >= 0; i--) {
      days.push({ date: prevMonthDays - i, isCurrentMonth: false });
    }

    // Days of current month
    for (let i = 1; i <= daysInMonth; i++) {
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;
      days.push({ date: i, isCurrentMonth: true, dateStr });
    }

    // Padding for days after last day (fill to 42 cells = 6 weeks)
    const remaining = 42 - days.length;
    for (let i = 1; i <= remaining; i++) {
      days.push({ date: i, isCurrentMonth: false });
    }

    return days;
  }, [currentDate]);

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

      {/* Main Grid: Calendar + Stats */}
      <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
        {/* Calendar */}
        <CardSpotlight className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
              <IconCalendar className="h-5 w-5 text-primary" />
              Календарь посещений
            </h3>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="icon" onClick={goToPrevMonth}>
                <IconChevronLeft className="h-4 w-4" />
              </Button>
              <span className="min-w-[140px] text-center font-medium">
                {MONTHS[currentDate.getMonth()]} {currentDate.getFullYear()}
              </span>
              <Button variant="ghost" size="icon" onClick={goToNextMonth}>
                <IconChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Weekday headers */}
          <div className="grid grid-cols-7 gap-1 mb-2">
            {WEEKDAYS.map((day) => (
              <div key={day} className="py-2 text-center text-xs font-medium text-muted-foreground">
                {day}
              </div>
            ))}
          </div>

          {/* Calendar grid */}
          <div className="grid grid-cols-7 gap-1">
            {calendarDays.map((day, idx) => {
              const status = day.dateStr ? attendanceMap[day.dateStr] : undefined;
              return (
                <div
                  key={idx}
                  className={cn(
                    "aspect-square rounded-lg flex items-center justify-center text-sm transition-all",
                    !day.isCurrentMonth && "text-muted-foreground/30",
                    day.isCurrentMonth && !status && "text-foreground hover:bg-accent/50",
                    status && STATUS_COLORS[status]
                  )}
                  title={status ? getStatusLabel(status) : undefined}
                >
                  {day.date}
                </div>
              );
            })}
          </div>

          {/* Legend */}
          <div className="mt-6 flex flex-wrap items-center gap-4 border-t border-border pt-4">
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded bg-green-500" />
              <span className="text-xs text-muted-foreground">Присутствовал</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded bg-yellow-500" />
              <span className="text-xs text-muted-foreground">Опоздание</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded bg-blue-500" />
              <span className="text-xs text-muted-foreground">Уваж. причина</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded bg-red-500" />
              <span className="text-xs text-muted-foreground">Пропуск</span>
            </div>
          </div>
        </CardSpotlight>

        {/* Stats sidebar */}
        <div className="space-y-4">
          {/* Overall percentage */}
          <CardSpotlight className="p-6">
            <div className="text-center">
              <p className="text-sm text-muted-foreground">Общая посещаемость</p>
              <p className="mt-2 text-5xl font-bold text-green-500">
                <NumberTicker value={Math.round(stats.attendance_rate)} />%
              </p>
              <p className="mt-1 text-xs text-muted-foreground">за семестр</p>
            </div>
          </CardSpotlight>

          {/* Individual stats */}
          <div className="grid grid-cols-2 gap-3">
            <StatCard icon={<IconCheck className="h-5 w-5" />} label="Присутствовал" value={stats.present} color="green" />
            <StatCard icon={<IconClock className="h-5 w-5" />} label="Опоздания" value={stats.late} color="yellow" />
            <StatCard icon={<IconAlertCircle className="h-5 w-5" />} label="Уваж. причина" value={stats.excused} color="blue" />
            <StatCard icon={<IconX className="h-5 w-5" />} label="Пропуски" value={stats.absent} color="red" />
          </div>
        </div>
      </div>
    </div>
  );
}

function getStatusLabel(status: AttendanceStatus): string {
  switch (status) {
    case 'present': return 'Присутствовал';
    case 'late': return 'Опоздание';
    case 'excused': return 'Уважительная причина';
    case 'absent': return 'Пропуск';
  }
}

function StatCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: number; color: 'green' | 'yellow' | 'blue' | 'red' }) {
  const colorClasses = {
    green: 'text-green-500 bg-green-500/10',
    yellow: 'text-yellow-500 bg-yellow-500/10',
    blue: 'text-blue-500 bg-blue-500/10',
    red: 'text-red-500 bg-red-500/10',
  };

  return (
    <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="p-4 rounded-xl border border-border bg-card">
      <div className={cn("flex h-10 w-10 items-center justify-center rounded-lg", colorClasses[color])}>
        {icon}
      </div>
      <p className="mt-2 text-2xl font-bold text-foreground">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </motion.div>
  );
}

function AttendanceSkeleton() {
  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div className="space-y-2"><Skeleton className="h-8 w-48" /><Skeleton className="h-4 w-32" /></div>
      <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
        <Skeleton className="h-[400px] rounded-xl" />
        <div className="space-y-4">
          <Skeleton className="h-32 rounded-xl" />
          <div className="grid grid-cols-2 gap-3">
            {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-24 rounded-xl" />)}
          </div>
        </div>
      </div>
    </div>
  );
}
