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

/** Format deadline based on new visibility system */
function formatDeadlineStatus(lab: DeadlinesListProps['labs'][0]): string {
  // Новая система: используем lessons_until_deadline_5
  if (lab.lessons_until_deadline_5 !== undefined && lab.lessons_until_deadline_5 !== null) {
    if (lab.deadline_5_status === 'expired') {
      return 'На 5 уже нельзя';
    }
    if (lab.lessons_until_deadline_5 === 0) {
      return 'Последняя пара на 5';
    }
    if (lab.lessons_until_deadline_5 === 1) {
      return 'Ещё 1 пара на 5';
    }
    return `Ещё ${lab.lessons_until_deadline_5} пар на 5`;
  }
  
  // Fallback на старую систему
  if (!lab.deadline_5_lessons) return 'Без дедлайна';
  if (lab.deadline_5_lessons === 1) return 'След. пара';
  return `Через ${lab.deadline_5_lessons - 1} пар`;
}

/** Check if deadline is urgent */
function isDeadlineUrgent(lab: DeadlinesListProps['labs'][0]): boolean {
  if (lab.lessons_until_deadline_5 !== undefined && lab.lessons_until_deadline_5 !== null) {
    return lab.lessons_until_deadline_5 <= 1 && lab.deadline_5_status !== 'expired';
  }
  return (lab.deadline_5_lessons ?? Infinity) <= 1;
}

/**
 * List of upcoming lab deadlines
 */
export function DeadlinesList({ labs, maxItems = 5 }: DeadlinesListProps) {
  // Filter out accepted, sort by urgency (lessons_until_deadline_5 or deadline_5_lessons)
  const sortedLabs = [...labs]
    .filter(l => l.submission?.status !== 'ACCEPTED')
    .sort((a, b) => {
      // Приоритет: lessons_until_deadline_5 (новая система), затем deadline_5_lessons
      const aDeadline = a.lessons_until_deadline_5 ?? a.deadline_5_lessons ?? Infinity;
      const bDeadline = b.lessons_until_deadline_5 ?? b.deadline_5_lessons ?? Infinity;
      return aDeadline - bDeadline;
    })
    .slice(0, maxItems);

  if (sortedLabs.length === 0) {
    // Различаем "нет лаб вообще" vs "все сданы"
    const hasAnyLabs = labs.length > 0;
    return (
      <div className="space-y-3">
        <SectionHeader />
        <EmptyState
          icon={<IconFlask className="h-8 w-8" />}
          title={hasAnyLabs ? "Все работы сданы!" : "Нет лабораторных работ"}
          description={hasAnyLabs ? "Отличная работа, так держать" : "Работы появятся здесь, когда преподаватель их добавит"}
        />
      </div>
    );
  }

  return (
    <Effect fade slide={{ direction: 'up', offset: 20 }} delay={300} inView inViewOnce>
      <div className="space-y-3">
        <SectionHeader />
        
        <div className="space-y-2">
          {sortedLabs.map((lab) => {
            const status = getLabStatus(lab);
            const badge = STATUS_BADGE[status];
            const isSoon = isDeadlineUrgent(lab);
            const isExpired = lab.deadline_5_status === 'expired';

            return (
              <Link
                key={lab.id}
                href={`/dashboard/labs/${lab.id}`}
                className={cn(
                  "flex items-center gap-3 p-3 rounded-lg",
                  "border border-border bg-card hover:bg-accent/50 transition-all hover:translate-x-1",
                  isSoon && status === 'not_submitted' && "border-orange-500/50 bg-orange-500/5",
                  isExpired && status === 'not_submitted' && "border-red-500/50 bg-red-500/5"
                )}
              >
                {/* Urgency indicator */}
                <div className={cn(
                  "w-1 h-12 rounded-full shrink-0",
                  isExpired && status === 'not_submitted' ? "bg-red-500" :
                  isSoon && status === 'not_submitted' ? "bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.4)]" :
                  status === 'rejected' ? "bg-red-500" :
                  status === 'pending' ? "bg-yellow-500" :
                  "bg-muted"
                )} />
                
                <div className="flex-1 min-w-0 mr-3">
                  <p className="font-medium text-sm text-foreground truncate">
                    {lab.title}
                  </p>
                  <p className={cn(
                    "text-xs",
                    isExpired && status === 'not_submitted' ? "text-red-500 font-medium" :
                    isSoon && status === 'not_submitted' ? "text-orange-500 font-medium" : 
                    "text-muted-foreground"
                  )}>
                    {formatDeadlineStatus(lab)}
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
