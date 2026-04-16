'use client';

import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { MagicCard } from '@/components/ui/magic-card';
import { SlidingNumber } from '@/components/animate-ui/primitives/texts/sliding-number';
import { Effect } from '@/components/animate-ui/primitives/effects/effect';
import { IconCheck, IconX, IconAlertTriangle } from '@tabler/icons-react';
import type { StatusHeroProps, AttestationStatus } from './types';
import { EmptyState } from './EmptyState';
import { LabProgressPlanSummary } from './LabProgressPlanSummary';

/** Get attestation status from data */
function getAttestationStatus(attestation: StatusHeroProps['attestation']): AttestationStatus {
  if (!attestation || attestation.error) return 'unavailable';
  if (attestation.is_passing) return 'passing';
  const pointsToPass = (attestation.min_passing_points || 18) - attestation.total_score;
  if (pointsToPass <= 5) return 'borderline';
  return 'failing';
}

/** Grade color config with subtle shine */
const GRADE_COLORS: Record<string, string> = {
  'отл': 'text-green-600 bg-gradient-to-r from-green-500/10 via-green-400/25 to-green-500/10 bg-[length:200%_100%] animate-shine [--duration:3s]',
  'хор': 'text-blue-600 bg-gradient-to-r from-blue-500/10 via-blue-400/25 to-blue-500/10 bg-[length:200%_100%] animate-shine [--duration:3s]',
  'уд': 'text-yellow-600 bg-gradient-to-r from-yellow-500/10 via-yellow-400/25 to-yellow-500/10 bg-[length:200%_100%] animate-shine [--duration:3s]',
  'неуд': 'text-red-600 bg-gradient-to-r from-red-500/10 via-red-400/25 to-red-500/10 bg-[length:200%_100%] animate-shine [--duration:3s]',
};

/** Status config for styling */
const STATUS_CONFIG = {
  passing: {
    icon: IconCheck,
    label: 'Зачёт получен',
    sublabel: 'Отличная работа!',
    gradient: '#22c55e20',
    color: 'text-green-500',
    border: 'border-green-500/30',
    bg: 'bg-green-500/5',
    progressGradient: 'from-green-500 to-emerald-400',
  },
  failing: {
    icon: IconAlertTriangle,
    label: 'На пути к зачёту',
    sublabel: 'Продолжай в том же духе',
    gradient: '#6366f120',
    color: 'text-indigo-500',
    border: 'border-indigo-500/30',
    bg: 'bg-indigo-500/5',
    progressGradient: 'from-indigo-500 to-purple-400',
  },
  borderline: {
    icon: IconAlertTriangle,
    label: 'Зачёт близко',
    sublabel: 'Ещё немного!',
    gradient: '#eab30820',
    color: 'text-yellow-500',
    border: 'border-yellow-500/30',
    bg: 'bg-yellow-500/5',
    progressGradient: 'from-yellow-500 to-amber-400',
  },
  unavailable: {
    icon: IconX,
    label: 'Нет данных',
    sublabel: '',
    gradient: '#71717a20',
    color: 'text-muted-foreground',
    border: 'border-border',
    bg: 'bg-muted/30',
    progressGradient: 'from-gray-500 to-gray-400',
  },
} as const;

/**
 * Hero section showing attestation status prominently
 */
export function StatusHero({ attestation, isLoading }: StatusHeroProps) {
  if (isLoading) {
    return <StatusHeroSkeleton />;
  }

  const status = getAttestationStatus(attestation);
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;

  if (status === 'unavailable') {
    return (
      <MagicCard gradientColor={config.gradient}>
        <div className={cn("p-6", config.border, config.bg, "border rounded-xl")}>
          <EmptyState
            icon={<Icon className="h-8 w-8" />}
            title="Данные аттестации недоступны"
            description="Информация появится после начала семестра"
          />
          <LabProgressPlanSummary attestation={attestation} />
        </div>
      </MagicCard>
    );
  }

  const maxPoints = attestation!.max_points || 40;
  const progressPercent = (attestation!.total_score / maxPoints) * 100;
  const labsBreakdown = attestation!.breakdown?.labs;
  const labsCount = labsBreakdown?.count || 0;
  const labsRequired = labsBreakdown?.required || 0;

  return (
    <Effect fade slide={{ direction: 'up', offset: 20 }} inView inViewOnce>
      <MagicCard gradientColor={config.gradient} className="overflow-hidden">
        <div className={cn("p-6", config.border, config.bg, "border rounded-xl")}>
          {/* Status Badge */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className={cn("p-2 rounded-full", config.bg)}>
                <Icon className={cn("h-6 w-6", config.color)} />
              </div>
              <div>
                <Badge variant="outline" className={cn("text-sm font-semibold", config.color)}>
                  {config.label}
                </Badge>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {config.sublabel}
                </p>
              </div>
            </div>
            {attestation!.grade && (
              <span className={cn(
                "text-sm font-semibold px-2 py-1 rounded-md",
                GRADE_COLORS[attestation!.grade] || "text-foreground"
              )}>
                Оценка: {attestation!.grade}
              </span>
            )}
          </div>

          {/* Score Display */}
          <div className="text-center mb-4">
            <div className="flex items-baseline justify-center gap-1">
              <span className={cn("text-5xl font-bold", config.color)}>
                <SlidingNumber number={Math.round(attestation!.total_score * 10) / 10} decimalPlaces={1} />
              </span>
              <span className="text-2xl text-muted-foreground">/{maxPoints}</span>
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              баллов из {maxPoints}
            </p>
          </div>

          {/* Progress Bar with gradient */}
          <div className="relative h-3 bg-muted/50 rounded-full overflow-hidden mb-4">
            <div 
              className={cn("h-full rounded-full bg-gradient-to-r transition-all duration-500", config.progressGradient)}
              style={{ width: `${Math.min(progressPercent, 100)}%` }}
            />
          </div>

          <LabProgressPlanSummary attestation={attestation} />

          {/* Labs info and points to pass */}
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            {labsRequired > 0 && (
              <span>
                Зачтено для аттестации:{' '}
                <span className={cn("font-semibold", labsCount >= labsRequired ? "text-green-500" : "text-foreground")}>
                  {labsCount}/{labsRequired}
                </span>
              </span>
            )}
            {status !== 'passing' && (
              <span>
                До зачёта: <span className="font-semibold text-foreground">{((attestation!.min_passing_points || 18) - attestation!.total_score).toFixed(1)} баллов</span>
              </span>
            )}
            {status === 'passing' && !labsRequired && (
              <span className="text-green-500">✓ Все требования выполнены</span>
            )}
          </div>
        </div>
      </MagicCard>
    </Effect>
  );
}

function StatusHeroSkeleton() {
  return (
    <MagicCard gradientColor="#71717a20">
      <div className="p-6 animate-pulse">
        <div className="h-8 w-24 bg-muted rounded mb-4" />
        <div className="h-12 w-32 bg-muted rounded mx-auto mb-4" />
        <div className="h-2 bg-muted rounded" />
      </div>
    </MagicCard>
  );
}
