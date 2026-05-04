'use client';

import Link from 'next/link';
import { AnimatePresence, motion } from 'motion/react';
import { IconCalendar, IconCheck, IconClock, IconFlask, IconHandStop, IconLock, IconPlayerPlay, IconX } from '@tabler/icons-react';
import type { StudentLab } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { DeadlineTraceBadges } from '@/components/labs/DeadlineTraceBadges';
import { cn } from '@/lib/utils';
import {
  getResolvedAcceptanceLabel,
  getResolvedLabGrade,
  getResolvedLabStatus,
  getResolvedLabStatusLabel,
} from '@/lib/labs/progress';

interface LabsGridProps {
  labs: StudentLab[];
  hoveredIndex: number | null;
  actionLoading: string | null;
  onHover: (index: number | null) => void;
  onMarkReady: (labId: string) => void;
  onCancelReady: (labId: string) => void;
}

type LabCardProps = Omit<LabsGridProps, 'labs'> & {
  lab: StudentLab;
  index: number;
};

function getStatusConfig(lab: StudentLab) {
  if (!lab.is_available) return { icon: IconLock, color: 'text-neutral-400', bg: 'bg-neutral-400/10', label: 'Заблокировано', border: 'border-neutral-500/20' };

  const status = getResolvedLabStatus(lab);
  switch (status) {
    case 'accepted': return { icon: IconCheck, color: 'text-green-500', bg: 'bg-green-500/10', label: getResolvedAcceptanceLabel(lab), border: 'border-green-500/30' };
    case 'pending': return { icon: IconClock, color: 'text-yellow-500', bg: 'bg-yellow-500/10', label: 'В очереди', border: 'border-yellow-500/30' };
    case 'rejected': return { icon: IconX, color: 'text-red-500', bg: 'bg-red-500/10', label: getResolvedLabStatusLabel(lab), border: 'border-red-500/30' };
    default: return { icon: IconFlask, color: 'text-blue-500', bg: 'bg-blue-500/10', label: 'Доступно', border: 'border-blue-500/20' };
  }
}

export function LabsGrid({ labs, hoveredIndex, actionLoading, onHover, onMarkReady, onCancelReady }: LabsGridProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {labs.map((lab, index) => (
        <LabCard
          key={lab.id}
          lab={lab}
          index={index}
          hoveredIndex={hoveredIndex}
          actionLoading={actionLoading}
          onHover={onHover}
          onMarkReady={onMarkReady}
          onCancelReady={onCancelReady}
        />
      ))}
    </div>
  );
}

function LabCard({ lab, index, hoveredIndex, actionLoading, onHover, onMarkReady, onCancelReady }: LabCardProps) {
  const status = getStatusConfig(lab);
  const StatusIcon = status.icon;
  const isLoading = actionLoading === lab.id;
  const resolvedGrade = getResolvedLabGrade(lab);
  const resolvedStatus = getResolvedLabStatus(lab);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03 }}
      className="relative group"
      onMouseEnter={() => onHover(index)}
      onMouseLeave={() => onHover(null)}
    >
      <AnimatePresence>
        {hoveredIndex === index && (
          <motion.span
            className="absolute inset-0 h-full w-full bg-neutral-200/50 dark:bg-neutral-800/50 block rounded-xl"
            layoutId="hoverBackground"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1, transition: { duration: 0.15 } }}
            exit={{ opacity: 0, transition: { duration: 0.15, delay: 0.2 } }}
          />
        )}
      </AnimatePresence>
      <div className={cn('relative z-10 p-4 rounded-xl border bg-card transition-all', !lab.is_available && 'opacity-60', status.border)}>
        <LabCardHeader lab={lab} status={status} StatusIcon={StatusIcon} resolvedGrade={resolvedGrade} resolvedStatus={resolvedStatus} />
        <h4 className="font-semibold text-foreground mb-1 line-clamp-2">{lab.title}</h4>
        {lab.topic && <p className="text-xs text-muted-foreground mb-2 line-clamp-1">{lab.topic}</p>}
        <p className={cn('text-sm mb-3', status.color)}>{status.label}</p>
        {lab.variant_number && (
          <div className="text-xs text-muted-foreground mb-3">
            Ваш вариант: <span className="font-semibold text-foreground">{lab.variant_number}</span>
          </div>
        )}
        <DeadlineTraceBadges trace={lab.deadline_trace} className="flex flex-wrap gap-2 mb-3" />
        <LabDeadlineNote lab={lab} />
        <LabActions
          lab={lab}
          isLoading={isLoading}
          resolvedStatus={resolvedStatus}
          onMarkReady={onMarkReady}
          onCancelReady={onCancelReady}
        />
      </div>
    </motion.div>
  );
}

function LabCardHeader({ lab, status, StatusIcon, resolvedGrade, resolvedStatus }: {
  lab: StudentLab;
  status: ReturnType<typeof getStatusConfig>;
  StatusIcon: typeof IconFlask;
  resolvedGrade?: number;
  resolvedStatus: ReturnType<typeof getResolvedLabStatus>;
}) {
  return (
    <div className="flex items-start justify-between mb-3">
      <div className="flex items-center gap-2">
        <div className={cn('p-2 rounded-lg', status.bg)}>
          <StatusIcon className={cn('h-5 w-5', status.color)} />
        </div>
        <span className="text-sm font-medium text-muted-foreground">№{lab.number}</span>
      </div>
      <Badge
        variant={lab.is_accepted ? 'default' : resolvedStatus === 'rejected' ? 'destructive' : 'secondary'}
        className={cn(lab.current_max_grade && lab.current_max_grade < lab.max_grade && resolvedGrade === undefined && 'bg-orange-500/10 text-orange-500 border-orange-500/30')}
      >
        {resolvedGrade !== undefined
          ? `${resolvedGrade}/${lab.max_grade}`
          : lab.current_max_grade && lab.current_max_grade < lab.max_grade
            ? `макс. ${lab.current_max_grade}`
            : `—/${lab.max_grade}`}
      </Badge>
    </div>
  );
}

function LabDeadlineNote({ lab }: { lab: StudentLab }) {
  return (
    <div className="flex items-center justify-between text-xs text-muted-foreground pt-3 border-t border-border">
      <div className="flex items-center gap-1">
        <IconCalendar className="h-3 w-3" />
        <span className={cn(
          lab.deadline_5_status === 'expired' && !lab.has_extension && 'text-red-500 font-medium',
          lab.has_extension && 'text-green-500 font-medium',
          lab.lessons_until_deadline_5 !== undefined && lab.lessons_until_deadline_5 !== null && lab.lessons_until_deadline_5 <= 1 && lab.deadline_5_status !== 'expired' && !lab.has_extension && 'text-orange-500 font-medium',
        )}>
          {getDeadlineLabel(lab)}
        </span>
      </div>
    </div>
  );
}

function getDeadlineLabel(lab: StudentLab) {
  if (lab.has_extension) return `+${lab.extension_bonus} пар (продление)`;
  if (lab.deadline_5_status === 'expired') return 'На 5 уже нельзя';
  if (lab.lessons_until_deadline_5 !== undefined && lab.lessons_until_deadline_5 !== null) {
    return lab.lessons_until_deadline_5 === 0 ? 'Последняя пара на 5' : `Ещё ${lab.lessons_until_deadline_5} пар на 5`;
  }
  return lab.deadline_5_lessons ? 'Дедлайн не активен' : 'Без дедлайна';
}

function LabActions({ lab, isLoading, resolvedStatus, onMarkReady, onCancelReady }: {
  lab: StudentLab;
  isLoading: boolean;
  resolvedStatus: ReturnType<typeof getResolvedLabStatus>;
  onMarkReady: (labId: string) => void;
  onCancelReady: (labId: string) => void;
}) {
  if (!lab.is_available) return <div className="mt-3 flex gap-2" />;

  return (
    <div className="mt-3 flex gap-2">
      <Link href={`/dashboard/labs/${lab.id}`} className="flex-1">
        <Button variant="outline" size="sm" className="w-full">Открыть</Button>
      </Link>
      {!lab.is_accepted && resolvedStatus === 'not_submitted' && (
        <Button size="sm" onClick={() => onMarkReady(lab.id)} disabled={isLoading}>
          {isLoading ? '...' : <><IconPlayerPlay className="h-4 w-4 mr-1" />Сдать</>}
        </Button>
      )}
      {!lab.is_accepted && lab.submission?.status === 'READY' && (
        <Button size="sm" variant="destructive" onClick={() => onCancelReady(lab.id)} disabled={isLoading}>
          {isLoading ? '...' : <><IconHandStop className="h-4 w-4 mr-1" />Отмена</>}
        </Button>
      )}
      {!lab.is_accepted && resolvedStatus === 'rejected' && (
        <Button size="sm" onClick={() => onMarkReady(lab.id)} disabled={isLoading}>
          {isLoading ? '...' : 'Пересдать'}
        </Button>
      )}
    </div>
  );
}
