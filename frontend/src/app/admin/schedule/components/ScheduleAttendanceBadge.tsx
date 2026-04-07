'use client';

import type {
  AttendanceSummaryState,
  GroupedLectureAttendanceSummaryResponse,
  LessonAttendanceSummaryResponse,
} from '@/lib/api/types/schedule';
import { AlertTriangle, CheckCircle2, Clock3 } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

export type ScheduleAttendanceSummary =
  | LessonAttendanceSummaryResponse
  | GroupedLectureAttendanceSummaryResponse;

interface AttendanceSummaryPresentation {
  badge_label: string;
  legend_label: string;
  tooltip: string;
  badge_class_name: string;
  dot_class_name: string;
  count_class_name: string;
  icon: typeof AlertTriangle;
}

const PRESENTATION_BY_STATE: Record<
  Exclude<AttendanceSummaryState, 'hidden' | 'not_applicable'>,
  AttendanceSummaryPresentation
> = {
  unmarked: {
    badge_label: 'Не отмечено',
    legend_label: 'Не выставлена',
    tooltip: 'Посещаемость не выставлена',
    badge_class_name:
      'border-red-500/45 bg-red-500/15 text-red-800 shadow-[0_0_0_1px_rgba(239,68,68,0.12),0_4px_18px_rgba(239,68,68,0.18)] dark:text-red-200',
    dot_class_name: 'bg-red-500',
    count_class_name: 'bg-red-500/15 text-red-900 dark:text-red-100',
    icon: AlertTriangle,
  },
  partial: {
    badge_label: 'Частично',
    legend_label: 'Частично',
    tooltip: 'Посещаемость выставлена частично',
    badge_class_name:
      'border-amber-500/45 bg-amber-500/15 text-amber-800 shadow-[0_0_0_1px_rgba(245,158,11,0.12),0_4px_18px_rgba(245,158,11,0.16)] dark:text-amber-200',
    dot_class_name: 'bg-amber-500',
    count_class_name: 'bg-amber-500/15 text-amber-900 dark:text-amber-100',
    icon: Clock3,
  },
  complete: {
    badge_label: 'Готово',
    legend_label: 'Выставлена',
    tooltip: 'Посещаемость выставлена',
    badge_class_name:
      'border-emerald-500/45 bg-emerald-500/15 text-emerald-800 shadow-[0_0_0_1px_rgba(16,185,129,0.12),0_4px_18px_rgba(16,185,129,0.16)] dark:text-emerald-200',
    dot_class_name: 'bg-emerald-500',
    count_class_name: 'bg-emerald-500/15 text-emerald-900 dark:text-emerald-100',
    icon: CheckCircle2,
  },
};

export const SCHEDULE_ATTENDANCE_LEGEND = (['unmarked', 'partial', 'complete'] as const).map((state) => ({
  state,
  ...PRESENTATION_BY_STATE[state],
}));

export function getAttendanceSummaryPresentation(summary?: ScheduleAttendanceSummary | null) {
  if (!summary || summary.state === 'hidden' || summary.state === 'not_applicable') {
    return null;
  }
  return PRESENTATION_BY_STATE[summary.state];
}

interface ScheduleAttendanceBadgeProps {
  summary?: ScheduleAttendanceSummary | null;
}

export function ScheduleAttendanceBadge({ summary }: ScheduleAttendanceBadgeProps) {
  const presentation = getAttendanceSummaryPresentation(summary);
  if (!presentation) {
    return null;
  }

  const counts = summary ? `${summary.marked_count}/${summary.expected_count}` : '';
  const tooltip = `${presentation.tooltip} (${counts})`;
  const Icon = presentation.icon;

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span
          className={cn(
            'inline-flex max-w-full items-center gap-1 rounded-md border px-1.5 py-1 text-[10px] font-semibold leading-none transition-transform duration-200 hover:-translate-y-0.5',
            presentation.badge_class_name
          )}
          aria-label={tooltip}
          title={tooltip}
        >
          <span className="relative flex h-2.5 w-2.5 shrink-0 items-center justify-center">
            <span className={cn('absolute inset-0 rounded-full opacity-35 blur-[2px]', presentation.dot_class_name)} />
            <span className={cn('relative h-2.5 w-2.5 rounded-full ring-2 ring-background', presentation.dot_class_name)} />
          </span>
          <Icon className="h-3 w-3 shrink-0" />
          <span className="tracking-[0.01em]">{presentation.badge_label}</span>
          <span
            className={cn(
              'rounded-sm px-1 py-0.5 font-bold tabular-nums',
              presentation.count_class_name
            )}
          >
            {counts}
          </span>
        </span>
      </TooltipTrigger>
      <TooltipContent side="top">{tooltip}</TooltipContent>
    </Tooltip>
  );
}
