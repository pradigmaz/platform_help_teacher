'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  CalendarCheck, 
  CheckCircle2, 
  Clock, 
  XCircle, 
  AlertCircle,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
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

interface AttendanceHistoryProps {
  history: AttendanceRecordPublic[];
  stats: AttendanceStats;
}

const STATUS_CONFIG = {
  present: {
    label: 'Присутствовал',
    shortLabel: 'Был',
    icon: CheckCircle2,
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
    badgeClass: 'bg-green-500/10 text-green-600 border-green-200',
  },
  late: {
    label: 'Опоздал',
    shortLabel: 'Опоздал',
    icon: Clock,
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500/10',
    badgeClass: 'bg-yellow-500/10 text-yellow-600 border-yellow-200',
  },
  excused: {
    label: 'Уважительная',
    shortLabel: 'Ув. причина',
    icon: AlertCircle,
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
    badgeClass: 'bg-blue-500/10 text-blue-600 border-blue-200',
  },
  absent: {
    label: 'Отсутствовал',
    shortLabel: 'Н/Б',
    icon: XCircle,
    color: 'text-red-500',
    bgColor: 'bg-red-500/10',
    badgeClass: 'bg-red-500/10 text-red-600 border-red-200',
  },
} as const;

type StatusKey = keyof typeof STATUS_CONFIG;

export function AttendanceHistory({ history, stats }: AttendanceHistoryProps) {
  const [expanded, setExpanded] = useState(false);
  const displayCount = expanded ? history.length : 10;
  const displayedHistory = history.slice(0, displayCount);
  const hasMore = history.length > 10;

  return (
    <Card>
      <CardHeader className="pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-2">
            <CalendarCheck className="h-5 w-5 text-muted-foreground" />
            <CardTitle>История посещений</CardTitle>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground">Посещаемость:</span>
            <Badge variant="outline" className={cn(
              stats.rate >= 80 ? 'bg-green-500/10 text-green-600' :
              stats.rate >= 60 ? 'bg-yellow-500/10 text-yellow-600' :
              'bg-red-500/10 text-red-600'
            )}>
              {Math.round(stats.rate)}%
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Stats Summary */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatBadge 
            status="present" 
            count={stats.present} 
            total={stats.total} 
          />
          <StatBadge 
            status="late" 
            count={stats.late} 
            total={stats.total} 
          />
          <StatBadge 
            status="excused" 
            count={stats.excused} 
            total={stats.total} 
          />
          <StatBadge 
            status="absent" 
            count={stats.absent} 
            total={stats.total} 
          />
        </div>

        {/* History List */}
        <div className="space-y-2">
          {displayedHistory.map((record, index) => (
            <AttendanceRow key={index} record={record} />
          ))}
        </div>

        {/* Show More Button */}
        {hasMore && (
          <Button
            variant="ghost"
            className="w-full"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? (
              <>
                <ChevronUp className="h-4 w-4 mr-2" />
                Свернуть
              </>
            ) : (
              <>
                <ChevronDown className="h-4 w-4 mr-2" />
                Показать все ({history.length})
              </>
            )}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

function StatBadge({ status, count, total }: { status: StatusKey; count: number; total: number }) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;
  const percent = total > 0 ? Math.round((count / total) * 100) : 0;

  return (
    <div className={cn("p-3 rounded-lg", config.bgColor)}>
      <div className="flex items-center gap-2">
        <Icon className={cn("h-4 w-4", config.color)} />
        <span className="text-sm font-medium">{config.shortLabel}</span>
      </div>
      <div className="mt-1 flex items-baseline gap-1">
        <span className="text-xl font-bold">{count}</span>
        <span className="text-xs text-muted-foreground">({percent}%)</span>
      </div>
    </div>
  );
}

function AttendanceRow({ record }: { record: AttendanceRecordPublic }) {
  const status = (record.status.toLowerCase() as StatusKey) || 'absent';
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.absent;
  const Icon = config.icon;

  const formattedDate = formatDate(record.date);

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors">
      <div className={cn("p-2 rounded-lg", config.bgColor)}>
        <Icon className={cn("h-4 w-4", config.color)} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm">{formattedDate}</p>
        {record.lesson_topic && (
          <p className="text-xs text-muted-foreground truncate">
            {record.lesson_topic}
          </p>
        )}
      </div>
      <Badge variant="outline" className={config.badgeClass}>
        {config.label}
      </Badge>
    </div>
  );
}

function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU', {
      weekday: 'short',
      day: 'numeric',
      month: 'long',
    });
  } catch {
    return dateStr;
  }
}
