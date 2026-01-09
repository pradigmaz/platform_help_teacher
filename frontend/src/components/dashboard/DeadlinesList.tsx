'use client';

import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Effect } from '@/components/animate-ui/primitives/effects/effect';
import { IconArrowRight, IconFlask } from '@tabler/icons-react';
import type { DeadlinesListProps, LabStatus } from './types';
import { EmptyState } from './EmptyState';

/** Get lab status */
function getLabStatus(lab: DeadlinesListProps['labs'][0]): LabStatus {
  if (!lab.submission) return 'not_submitted';
  switch (lab.submission.status) {
    case 'ACCEPTED': return 'accepted';
    case 'REJECTED': return 'rejected';
    case 'IN_REVIEW':
    case 'READY': return 'pending';
    default: return 'not_submitted';
  }
}

/** Status badge config */
const STATUS_BADGE = {
  accepted: { label: 'Принято', variant: 'default' as const, className: 'bg-green-500' },
  pending: { label: 'Проверка', variant: 'secondary' as const, className: '' },
  rejected: { label: 'Отклонено', variant: 'destructive' as const, className: '' },
  not_submitted: { label: 'Не сдано', variant: 'outline' as const, className: '' },
} as const;

/** Format deadline date */
function formatDeadline(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' });
}

/** Check if deadline is soon (within 3 days) */
function isDeadlineSoon(dateStr: string): boolean {
  const deadline = new Date(dateStr);
  const now = new Date();
  const diffDays = (deadline.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
  return diffDays >= 0 && diffDays <= 3;
}

/**
 * List of upcoming lab deadlines
 */
export function DeadlinesList({ labs, maxItems = 5 }: DeadlinesListProps) {
  // Sort by deadline, filter out accepted
  const sortedLabs = [...labs]
    .filter(l => l.submission?.status !== 'ACCEPTED')
    .sort((a, b) => {
      if (!a.deadline) return 1;
      if (!b.deadline) return -1;
      return new Date(a.deadline).getTime() - new Date(b.deadline).getTime();
    })
    .slice(0, maxItems);

  if (sortedLabs.length === 0) {
    return (
      <div className="space-y-3">
        <SectionHeader />
        <EmptyState
          icon={<IconFlask className="h-8 w-8" />}
          title="Все работы сданы!"
          description="Отличная работа, так держать"
        />
      </div>
    );
  }

  return (
    <Effect fade slide={{ direction: 'up', offset: 20 }} delay={300} inView inViewOnce>
      <div className="space-y-3">
        <SectionHeader />
        
        <div className="space-y-2">
          {sortedLabs.map((lab, idx) => {
            const status = getLabStatus(lab);
            const badge = STATUS_BADGE[status];
            const isSoon = lab.deadline && isDeadlineSoon(lab.deadline);

            return (
              <Link
                key={lab.id}
                href={`/dashboard/labs/${lab.id}`}
                className={cn(
                  "flex items-center justify-between p-3 rounded-lg",
                  "border border-border bg-card hover:bg-accent/50 transition-colors",
                  isSoon && status === 'not_submitted' && "border-orange-500/50 bg-orange-500/5"
                )}
              >
                <div className="flex-1 min-w-0 mr-3">
                  <p className="font-medium text-sm text-foreground truncate">
                    {lab.title}
                  </p>
                  <p className={cn(
                    "text-xs",
                    isSoon && status === 'not_submitted' ? "text-orange-500 font-medium" : "text-muted-foreground"
                  )}>
                    {lab.deadline ? formatDeadline(lab.deadline) : 'Без дедлайна'}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <Badge variant={badge.variant} className={cn("text-xs", badge.className)}>
                    {badge.label}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {lab.submission?.grade !== undefined 
                      ? `${lab.submission.grade}/${lab.max_grade}`
                      : `—/${lab.max_grade}`
                    }
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </Effect>
  );
}

function SectionHeader() {
  return (
    <div className="flex items-center justify-between">
      <h3 className="text-base font-semibold text-foreground">Ближайшие работы</h3>
      <Link
        href="/dashboard/labs"
        className="text-xs text-muted-foreground hover:text-primary flex items-center gap-1"
      >
        Все работы <IconArrowRight className="h-3 w-3" />
      </Link>
    </div>
  );
}
