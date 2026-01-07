'use client';

import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { MagicCard } from '@/components/ui/magic-card';
import { SlidingNumber } from '@/components/animate-ui/primitives/texts/sliding-number';
import { Effect } from '@/components/animate-ui/primitives/effects/effect';
import { IconCheck, IconX, IconAlertTriangle } from '@tabler/icons-react';
import type { StatusHeroProps, AttestationStatus } from './types';
import { EmptyState } from './EmptyState';

/** Get attestation status from data */
function getAttestationStatus(attestation: StatusHeroProps['attestation']): AttestationStatus {
  if (!attestation || attestation.error) return 'unavailable';
  if (attestation.is_passing) return 'passing';
  const pointsToPass = (attestation.min_passing_points || 18) - attestation.total_score;
  if (pointsToPass <= 5) return 'borderline';
  return 'failing';
}

/** Status config for styling */
const STATUS_CONFIG = {
  passing: {
    icon: IconCheck,
    label: 'Зачёт',
    gradient: '#22c55e20',
    color: 'text-green-500',
    border: 'border-green-500/30',
    bg: 'bg-green-500/5',
  },
  failing: {
    icon: IconX,
    label: 'Незачёт',
    gradient: '#ef444420',
    color: 'text-red-500',
    border: 'border-red-500/30',
    bg: 'bg-red-500/5',
  },
  borderline: {
    icon: IconAlertTriangle,
    label: 'Почти зачёт',
    gradient: '#eab30820',
    color: 'text-yellow-500',
    border: 'border-yellow-500/30',
    bg: 'bg-yellow-500/5',
  },
  unavailable: {
    icon: IconX,
    label: 'Нет данных',
    gradient: '#71717a20',
    color: 'text-muted-foreground',
    border: 'border-border',
    bg: 'bg-muted/30',
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
        <EmptyState
          icon={<Icon className="h-8 w-8" />}
          title="Данные аттестации недоступны"
          description="Информация появится после начала семестра"
        />
      </MagicCard>
    );
  }

  const maxPoints = attestation!.max_points || 40;
  const progressPercent = (attestation!.total_score / maxPoints) * 100;

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
                {attestation!.grade && (
                  <span className="ml-2 text-xs text-muted-foreground">
                    Оценка: {attestation!.grade}
                  </span>
                )}
              </div>
            </div>
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

          {/* Progress Bar */}
          <Progress 
            value={progressPercent}
            className={cn("h-2", `[&>div]:${config.color.replace('text-', 'bg-')}`)}
          />

          {/* Points to pass hint */}
          {status !== 'passing' && (
            <p className="text-xs text-center text-muted-foreground mt-3">
              До зачёта: {((attestation!.min_passing_points || 18) - attestation!.total_score).toFixed(1)} баллов
            </p>
          )}
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
