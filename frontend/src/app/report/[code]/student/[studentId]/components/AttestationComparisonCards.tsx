'use client';

import { MetricCard } from '@/components/ui/metric-card';
import type { StudentDetailData } from '@/lib/api';
import { buildAttestationSummary } from './attestationSummary';

interface AttestationComparisonCardsProps {
  firstAttestationData: StudentDetailData;
  currentAttestationData: StudentDetailData;
}

export function AttestationComparisonCards({
  firstAttestationData,
  currentAttestationData,
}: AttestationComparisonCardsProps) {
  const previous = buildAttestationSummary(firstAttestationData, 'first');
  const current = buildAttestationSummary(currentAttestationData, 'second');
  const scoreDelta = current.totalScore - previous.totalScore;
  const averageDelta =
    current.groupAverage !== undefined && previous.groupAverage !== undefined
      ? (current.totalScore - current.groupAverage) - (previous.totalScore - previous.groupAverage)
      : null;
  const statusSummary = describeStatusShift(previous.isPassing, current.isPassing);

  return (
    <section className="space-y-3">
      <div className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
          Аттестации
        </p>
        <h2 className="text-lg font-semibold text-foreground">Как изменился результат</h2>
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <MetricCard interactive={false} tint="neutral">
          <div className="space-y-4 p-5">
            <div className="space-y-1">
              <p className="text-sm font-medium text-foreground">{previous.attestationLabel}</p>
              <p className="text-sm text-muted-foreground">Предыдущий результат</p>
            </div>
            <div className="space-y-2">
              <div className="flex items-end justify-between gap-3">
                <p className="text-3xl font-semibold tracking-tight text-foreground">
                  {previous.totalScore.toFixed(1)}
                </p>
                <p className="text-sm text-muted-foreground">/ {previous.maxPoints.toFixed(1)}</p>
              </div>
              <p className="text-base font-semibold text-foreground">{previous.statusLabel}</p>
              <p className="text-sm text-muted-foreground">{previous.gradeSummary}</p>
              {previous.averageSummary && (
                <p className="text-sm text-muted-foreground">{previous.averageSummary}</p>
              )}
            </div>
          </div>
        </MetricCard>

        <MetricCard interactive={false} tint="green">
          <div className="space-y-4 p-5">
            <div className="space-y-1">
              <p className="text-sm font-medium text-foreground">Изменение к текущей аттестации</p>
              <p className="text-sm text-muted-foreground">{statusSummary}</p>
            </div>
            <div className="space-y-2">
              <p className="text-3xl font-semibold tracking-tight text-foreground">
                {formatDelta(scoreDelta)} балла
              </p>
              <p className="text-sm text-muted-foreground">
                С {previous.totalScore.toFixed(1)} / {previous.maxPoints.toFixed(1)} до{' '}
                {current.totalScore.toFixed(1)} / {current.maxPoints.toFixed(1)}
              </p>
              {averageDelta !== null && (
                <p className="text-sm text-muted-foreground">
                  Относительно среднего: {formatDelta(averageDelta)}
                </p>
              )}
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <CompactFact label="Было" value={previous.totalScore.toFixed(1)} />
              <CompactFact label="Сейчас" value={current.totalScore.toFixed(1)} />
              <CompactFact label="Рост" value={formatDelta(scoreDelta)} />
            </div>
          </div>
        </MetricCard>
      </div>
    </section>
  );
}

function CompactFact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border/60 bg-background/70 px-3 py-2">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-base font-semibold text-foreground">{value}</p>
    </div>
  );
}

function formatDelta(value: number): string {
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(1)}`;
}

function describeStatusShift(previousPassing: boolean, currentPassing: boolean): string {
  if (!previousPassing && currentPassing) {
    return 'Во второй аттестации порог уже закрыт';
  }
  if (previousPassing && !currentPassing) {
    return 'Текущий результат просел ниже порога';
  }
  if (currentPassing) {
    return 'Статус сохранился: зачёт получен';
  }
  return 'Статус сохранился: баллы ещё нужно добрать';
}
