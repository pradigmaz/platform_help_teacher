'use client';

import { useMemo, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { CalendarCheck, CheckCircle2, ChevronDown, ChevronUp, Clock, ShieldAlert, XCircle } from 'lucide-react';
import { AttendanceRecordPublic } from '@/lib/api';
import { getLessonTypeConfig } from '@/lib/schedule-constants';
import { cn } from '@/lib/utils';

interface AttendanceStats {
  present: number;
  late: number;
  excused: number;
  absent: number;
  total: number;
  rate: number;
}

interface AttendanceHistoryProps {
  history: AttendanceRecordPublic[];
  stats: AttendanceStats;
}

const STATUS_CONFIG = {
  present: {
    label: 'Присутствовал',
    compactLabel: 'Был(а)',
    icon: CheckCircle2,
    className: 'border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
  },
  late: {
    label: 'Опоздал',
    compactLabel: 'Опоздание',
    icon: Clock,
    className: 'border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-300',
  },
  excused: {
    label: 'Уважительная причина',
    compactLabel: 'Уважительная',
    icon: ShieldAlert,
    className: 'border-blue-500/20 bg-blue-500/10 text-blue-700 dark:text-blue-300',
  },
  absent: {
    label: 'Отсутствовал',
    compactLabel: 'Пропуск',
    icon: XCircle,
    className: 'border-red-500/20 bg-red-500/10 text-red-700 dark:text-red-300',
  },
} as const;

type StatusKey = keyof typeof STATUS_CONFIG;

export function AttendanceHistory({ history, stats }: AttendanceHistoryProps) {
  const [expanded, setExpanded] = useState(false);
  const sortedHistory = useMemo(
    () => [...history].sort((left, right) => new Date(right.date).getTime() - new Date(left.date).getTime()),
    [history],
  );
  const primaryTimeline = sortedHistory.slice(0, 6);
  const attendedCount = stats.present + stats.late;
  const attendanceTone =
    stats.rate >= 80 ? 'text-emerald-700 dark:text-emerald-300'
    : stats.rate >= 60 ? 'text-amber-700 dark:text-amber-300'
    : 'text-red-700 dark:text-red-300';

  return (
    <Card className="group relative overflow-hidden border-border/60 bg-card/95 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/25 hover:bg-accent/10 hover:shadow-lg focus-within:border-primary/25 focus-within:shadow-lg">
      <div className="pointer-events-none absolute inset-x-6 top-0 h-px bg-gradient-to-r from-transparent via-green-500/35 to-transparent" />
      <div className="pointer-events-none absolute -right-10 -top-10 h-28 w-28 rounded-full bg-green-500/15 opacity-0 blur-3xl transition-opacity duration-200 group-hover:opacity-100 group-focus-within:opacity-100" />
      <CardHeader className="space-y-4 border-b border-border/60 bg-muted/20 pb-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <CalendarCheck className="h-5 w-5 text-muted-foreground" />
              <CardTitle className="text-lg">Посещаемость за период</CardTitle>
            </div>
            <p className="text-sm text-muted-foreground">
              Был(а) на {attendedCount} из {stats.total} занятий за выбранную аттестацию.
            </p>
          </div>
          <Badge variant="outline" className={`rounded-full border px-3 py-1 text-sm font-medium ${attendanceTone}`}>
            {Math.round(stats.rate)}%
          </Badge>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <AttendanceStatCard label="Был(а)" value={stats.present} tone="present" />
          <AttendanceStatCard label="Опоздания" value={stats.late} tone="late" />
          <AttendanceStatCard label="Уважительные" value={stats.excused} tone="excused" />
          <AttendanceStatCard label="Пропуски" value={stats.absent} tone="absent" />
        </div>
      </CardHeader>

      <CardContent className="space-y-4 p-6">
        <div className="space-y-1">
          <p className="text-sm font-medium text-foreground">Хронология занятий</p>
          <p className="text-sm text-muted-foreground">
            Сначала показываются последние занятия, чтобы было легче быстро оценить динамику.
          </p>
        </div>

        <div className="space-y-3">
          {primaryTimeline.map((record, index) => (
            <AttendanceRow key={`${record.date}-${index}`} record={record} />
          ))}
        </div>

        {sortedHistory.length > 6 && (
          <Collapsible open={expanded} onOpenChange={setExpanded} className="rounded-2xl border border-border/60 bg-muted/10">
            <div className="flex items-center justify-between gap-3 px-4 py-3">
              <div>
                <p className="text-sm font-medium text-foreground">
                  {expanded ? 'Свернуть подробную хронологию' : `Показать ещё ${sortedHistory.length - 6} занятий`}
                </p>
                <p className="text-xs text-muted-foreground">
                  Полный список по выбранному периоду аттестации
                </p>
              </div>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="sm">
                  {expanded ? (
                    <>
                      <ChevronUp className="mr-2 h-4 w-4" />
                      Свернуть
                    </>
                  ) : (
                    <>
                      <ChevronDown className="mr-2 h-4 w-4" />
                      Показать
                    </>
                  )}
                </Button>
              </CollapsibleTrigger>
            </div>
            <CollapsibleContent className="space-y-3 border-t border-border/60 px-4 pb-4 pt-3">
              {sortedHistory.slice(6).map((record, index) => (
                <AttendanceRow key={`${record.date}-extra-${index}`} record={record} />
              ))}
            </CollapsibleContent>
          </Collapsible>
        )}
      </CardContent>
    </Card>
  );
}

function AttendanceStatCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: StatusKey;
}) {
  const config = STATUS_CONFIG[tone];
  const Icon = config.icon;

  return (
    <div className={cn('rounded-2xl border px-4 py-3', config.className)}>
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4" />
        <span className="text-sm font-medium">{label}</span>
      </div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
    </div>
  );
}

function AttendanceRow({ record }: { record: AttendanceRecordPublic }) {
  const status = normalizeStatus(record.status);
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;

  return (
    <div className="flex items-start gap-3 rounded-2xl border border-border/60 bg-background/80 px-4 py-3">
      <div className={cn('mt-0.5 flex h-10 w-10 items-center justify-center rounded-xl border', config.className)}>
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-sm font-medium text-foreground">{formatDate(record.date)}</p>
          <Badge variant="outline" className={cn('rounded-full border px-2 py-0.5 text-[11px]', config.className)}>
            {config.compactLabel}
          </Badge>
          {record.lesson_type && (
            <Badge variant="secondary" className="rounded-full px-2 py-0.5 text-[11px]">
              {formatLessonType(record.lesson_type)}
            </Badge>
          )}
        </div>
        <p className="text-sm text-muted-foreground">
          {record.lesson_topic || 'Тема занятия не указана'}
        </p>
      </div>
    </div>
  );
}

function normalizeStatus(status: string): StatusKey {
  const normalized = status.toLowerCase();

  if (normalized === 'present') return 'present';
  if (normalized === 'late') return 'late';
  if (normalized === 'excused') return 'excused';
  return 'absent';
}

function formatDate(dateStr: string) {
  try {
    return new Date(dateStr).toLocaleDateString('ru-RU', {
      weekday: 'short',
      day: 'numeric',
      month: 'long',
    });
  } catch {
    return dateStr;
  }
}

function formatLessonType(lessonType: string) {
  return getLessonTypeConfig(lessonType).label;
}
