'use client';

import { LESSON_TYPE_CONFIG } from '@/lib/schedule-constants';
import { SCHEDULE_ATTENDANCE_LEGEND } from './ScheduleAttendanceBadge';

interface ScheduleLegendProps {
  lastUpdated?: string;
}

export function ScheduleLegend({ lastUpdated }: ScheduleLegendProps) {
  const types = [
    { key: 'lecture', config: LESSON_TYPE_CONFIG.lecture },
    { key: 'lab', config: LESSON_TYPE_CONFIG.lab },
    { key: 'practice', config: LESSON_TYPE_CONFIG.practice },
  ];

  return (
    <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
      {types.map(({ key, config }) => (
        <div key={key} className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${config.dot}`} />
          <span>{config.label}</span>
        </div>
      ))}
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full bg-destructive" />
        <span>Отменено</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full bg-yellow-500" />
        <span>Отпустил</span>
      </div>
      {SCHEDULE_ATTENDANCE_LEGEND.map((item) => (
        <div key={item.state} className="flex items-center gap-2">
          <div className={`h-3 w-3 rounded-full ${item.dot_class_name}`} />
          <span>{item.legend_label}</span>
        </div>
      ))}
      {lastUpdated && (
        <div className="ml-auto text-muted-foreground/70">
          Обновлено: {lastUpdated}
        </div>
      )}
    </div>
  );
}
