'use client';

import { Progress } from '@/components/ui/progress';
import { MetricCard } from '@/components/ui/metric-card';
import { NumberTicker } from '@/components/ui/number-ticker';
import { ShineBorder } from '@/components/ui/shine-border';
import { StudentDetailData } from '@/lib/api';
import { AlertTriangle, CheckCircle2, Clock3 } from 'lucide-react';
import type { ReportAttestation } from '../../../reportNavigation';
import { buildAttestationSummary } from './attestationSummary';

interface HeroCardProps {
  data: StudentDetailData;
  attestationType: ReportAttestation;
}

export function HeroCard({ data, attestationType }: HeroCardProps) {
  const summary = buildAttestationSummary(data, attestationType);
  const tone = summary.isEarlySemester ? 'blue' : summary.isPassing ? 'green' : 'red';
  const statusConfig =
    summary.statusKind === 'in_progress'
      ? {
          icon: Clock3,
          progressClassName: '[&>div]:bg-blue-500',
        }
      : summary.statusKind === 'passing'
        ? {
            icon: CheckCircle2,
            progressClassName: '[&>div]:bg-green-500',
          }
        : {
            icon: AlertTriangle,
            progressClassName: '[&>div]:bg-red-500',
          };
  const StatusIcon = statusConfig.icon;

  return (
    <MetricCard className="relative" interactive={false} tint={tone}>
      <div className="space-y-6 p-6">
        <div className="space-y-3">
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
            {summary.attestationLabel}
          </p>
          <div className="grid gap-4 lg:grid-cols-[minmax(0,1.3fr)_minmax(240px,0.7fr)]">
            <div className="space-y-3 rounded-3xl border border-border/60 bg-muted/20 p-5">
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                Общая оценка ситуации
              </p>
              <div className="space-y-1">
                <p className="flex items-center gap-2 text-xl font-semibold text-foreground">
                  <StatusIcon className="h-5 w-5 shrink-0" />
                  <span>{summary.statusLabel}</span>
                </p>
                <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
                  {summary.statusMessage}
                </p>
                {summary.averageSummary && (
                  <p className="text-sm text-muted-foreground">{summary.averageSummary}</p>
                )}
              </div>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                <MiniFact label="Порог зачёта" value={summary.minPassing.toFixed(1)} />
                <MiniFact label="Максимум" value={summary.maxPoints.toFixed(1)} />
                {summary.groupAverage !== undefined && (
                  <MiniFact label="Среднее по группе" value={summary.groupAverage.toFixed(1)} />
                )}
              </div>
            </div>

            <div className="rounded-3xl border border-border/60 bg-background/80 p-5">
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                Итоговый балл
              </p>
              <div className="mt-3 flex items-end gap-3">
                <div className="text-5xl font-semibold tracking-tight text-foreground">
                  <NumberTicker value={summary.totalScore} decimalPlaces={1} delay={0.15} />
                </div>
                <div className="pb-1 text-sm text-muted-foreground">/ {summary.maxPoints.toFixed(1)}</div>
              </div>
              <p className="mt-4 text-sm text-muted-foreground">{summary.gradeSummary}</p>
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between gap-3 text-xs text-muted-foreground">
            <span>0</span>
            <span>Порог: {summary.minPassing.toFixed(1)}</span>
            <span>{summary.maxPoints.toFixed(1)}</span>
          </div>
          <div className="relative">
            <Progress
              value={summary.progressPercent}
              className={`h-3 rounded-full ${statusConfig.progressClassName}`}
            />
            <div
              className="absolute inset-y-0 w-0.5 bg-yellow-500"
              style={{ left: `${(summary.minPassing / Math.max(summary.maxPoints, 1)) * 100}%` }}
            />
          </div>
        </div>
      </div>
      {summary.isExcellent && !summary.isEarlySemester && (
        <ShineBorder shineColor={['#fbbf24', '#f59e0b', '#d97706']} borderWidth={2} duration={8} />
      )}
    </MetricCard>
  );
}

function MiniFact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border/60 bg-background/80 px-4 py-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-lg font-semibold text-foreground">{value}</p>
    </div>
  );
}
