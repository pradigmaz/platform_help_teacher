'use client';

import { cn } from '@/lib/utils';
import { Label } from '@/components/ui/label';
import type { LessonStatus as LessonStatusType } from '../types';

interface LessonStatusProps {
  status: LessonStatusType;
  onChange: (status: LessonStatusType) => void;
}

const STATUS_OPTIONS = [
  { id: 'normal', label: 'Обычное' },
  { id: 'cancelled', label: 'Отменено' },
  { id: 'early', label: 'Отпустил' }
] as const;

export function LessonStatus({ status, onChange }: LessonStatusProps) {
  return (
    <div className="space-y-2">
      <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
        Статус занятия
      </Label>
      <div className="flex p-1 bg-muted rounded-lg">
        {STATUS_OPTIONS.map((opt) => (
          <button
            key={opt.id}
            onClick={() => onChange(opt.id)}
            className={cn(
              'flex-1 py-1.5 text-xs font-medium rounded-md transition-all',
              status === opt.id
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
