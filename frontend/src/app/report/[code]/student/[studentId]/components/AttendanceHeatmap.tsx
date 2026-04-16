'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CalendarCheck, CheckCircle2, Clock, XCircle, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { AttendanceRecordPublic } from '@/lib/api';

interface AttendanceStats {
  present: number;
  late: number;
  excused: number;
  absent: number;
  total: number;
  rate: number;
}

interface AttendanceHeatmapProps {
  history: AttendanceRecordPublic[];
  stats: AttendanceStats;
}

const STATUS_CONFIG = {
  present: {
    label: 'Был(а)',
    color: 'bg-emerald-500/20 border-emerald-500/30 text-emerald-500',
    dotColor: 'bg-emerald-400',
  },
  late: {
    label: 'Опоздал',
    color: 'bg-amber-500/20 border-amber-500/30 text-amber-500',
    dotColor: 'bg-amber-400',
  },
  excused: {
    label: 'Ув.',
    color: 'bg-blue-500/20 border-blue-500/30 text-blue-500',
    dotColor: 'bg-blue-400',
  },
  absent: {
    label: 'Н/Б',
    color: 'bg-red-500/20 border-red-500/30 text-red-500',
    dotColor: 'bg-red-400',
  },
} as const;

type StatusKey = keyof typeof STATUS_CONFIG;

export function AttendanceHeatmap({ history, stats }: AttendanceHeatmapProps) {
  // Сортируем по дате
  const sortedHistory = [...history].sort((a, b) => 
    new Date(a.date).getTime() - new Date(b.date).getTime()
  );

  return (
    <Card>
      <CardHeader className="pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-2">
            <CalendarCheck className="h-5 w-5 text-muted-foreground" />
            <CardTitle>Посещения за период</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              {stats.present + stats.late} из {stats.total} занятий в периоде
            </span>
            <Badge variant="outline" className={cn(
              stats.rate >= 80 ? 'bg-emerald-500/10 text-emerald-600 border-emerald-200' :
              stats.rate >= 60 ? 'bg-amber-500/10 text-amber-600 border-amber-200' :
              'bg-red-500/10 text-red-600 border-red-200'
            )}>
              {Math.round(stats.rate)}%
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Heatmap Grid */}
        <div className="overflow-x-auto pb-2">
          <div className="flex flex-wrap gap-2 min-w-fit">
            {sortedHistory.map((record, idx) => {
              const status = (record.status.toLowerCase() as StatusKey) || 'absent';
              const config = STATUS_CONFIG[status] || STATUS_CONFIG.absent;
              const date = new Date(record.date);
              const day = date.getDate();
              const month = date.toLocaleDateString('ru-RU', { month: 'short' }).replace('.', '');
              
              return (
                <div
                  key={idx}
                  title={`${date.toLocaleDateString('ru-RU')} — ${config.label}${record.lesson_topic ? `: ${record.lesson_topic}` : ''}`}
                  className={cn(
                    "w-10 h-10 sm:w-12 sm:h-12 rounded-lg flex flex-col items-center justify-center",
                    "border transition-transform hover:scale-105 cursor-default",
                    config.color
                  )}
                >
                  <span className="text-xs sm:text-sm font-bold">{day}</span>
                  <span className="text-[8px] sm:text-[10px] uppercase opacity-80">{month}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-4 text-xs text-muted-foreground pt-2 border-t">
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <span>Был(а) ({stats.present})</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <span>Опоздал ({stats.late})</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-blue-500" />
            <span>Ув. причина ({stats.excused})</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
            <span>Пропуск ({stats.absent})</span>
          </div>
        </div>

        {/* Stats Summary - компактные карточки */}
        <div className="grid grid-cols-4 gap-2">
          <StatMini icon={CheckCircle2} value={stats.present} label="Был(а)" color="emerald" />
          <StatMini icon={Clock} value={stats.late} label="Опоздал" color="amber" />
          <StatMini icon={AlertCircle} value={stats.excused} label="Ув." color="blue" />
          <StatMini icon={XCircle} value={stats.absent} label="Н/Б" color="red" />
        </div>
      </CardContent>
    </Card>
  );
}

interface StatMiniProps {
  icon: React.ComponentType<{ className?: string }>;
  value: number;
  label: string;
  color: 'emerald' | 'amber' | 'blue' | 'red';
}

function StatMini({ icon: Icon, value, label, color }: StatMiniProps) {
  const colorClasses = {
    emerald: 'bg-emerald-500/10 text-emerald-500',
    amber: 'bg-amber-500/10 text-amber-500',
    blue: 'bg-blue-500/10 text-blue-500',
    red: 'bg-red-500/10 text-red-500',
  };

  return (
    <div className={cn("p-2 rounded-lg text-center", colorClasses[color])}>
      <Icon className="h-4 w-4 mx-auto mb-1" />
      <div className="text-lg font-bold">{value}</div>
      <div className="text-[10px] opacity-80">{label}</div>
    </div>
  );
}
