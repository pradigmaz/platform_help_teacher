'use client';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { MetricCard } from '@/components/ui/metric-card';
import { NumberTicker } from '@/components/ui/number-ticker';
import { ShineBorder } from '@/components/ui/shine-border';
import { formatGroupCode } from '@/lib/utils';
import { StudentDetailData } from '@/lib/api';
import {
  AlertTriangle,
  ArrowLeft,
  Award,
  CheckCircle2,
  Clock3,
  Sparkles,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import type { ReportAttestation } from '../../../reportNavigation';

interface HeroCardProps {
  data: StudentDetailData;
  attestationType: ReportAttestation;
  studentId: string;
  onBack: () => void;
}

export function HeroCard({ data, attestationType, studentId, onBack }: HeroCardProps) {
  const maxPoints = data.max_points || 35;
  const minPassing = data.min_passing_points || 20;
  const totalScore = data.total_score || 0;
  const isPassing = data.is_passing ?? totalScore >= minPassing;
  const isEarlySemester = data.is_early_semester ?? false;
  const progressPercent = Math.min((totalScore / Math.max(maxPoints, 1)) * 100, 100);
  const differenceToPassing = Math.max(minPassing - totalScore, 0);
  const groupAverage = data.group_average_score;
  const comparisonDelta = groupAverage === undefined ? null : totalScore - groupAverage;
  const isExcellent = totalScore >= maxPoints * 0.85;
  const tone = isEarlySemester ? 'blue' : isPassing ? 'green' : 'red';
  const attestationLabel = attestationType === 'second' ? '2 аттестация' : '1 аттестация';
  const studentName = data.name || `Студент ${studentId.slice(0, 8)}`;

  const statusConfig = isEarlySemester
    ? {
        icon: Clock3,
        label: 'Семестр в процессе',
        message: 'Пока важнее динамика, чем итоговая оценка.',
        className: 'bg-blue-500/10 text-blue-700 dark:text-blue-300 border-blue-500/20',
        progressClassName: '[&>div]:bg-blue-500',
      }
    : isPassing
      ? {
          icon: CheckCircle2,
          label: 'Зачёт получен',
          message: 'Текущий результат уже выше порога.',
          className: 'bg-green-500/10 text-green-700 dark:text-green-300 border-green-500/20',
          progressClassName: '[&>div]:bg-green-500',
        }
      : {
          icon: AlertTriangle,
          label: 'Нужно добрать баллы',
          message: `До зачёта не хватает ${differenceToPassing.toFixed(1)} балла.`,
          className: 'bg-red-500/10 text-red-700 dark:text-red-300 border-red-500/20',
          progressClassName: '[&>div]:bg-red-500',
        };

  const StatusIcon = statusConfig.icon;
  const averageStatus =
    comparisonDelta === null
      ? null
      : comparisonDelta > 0
        ? {
            icon: TrendingUp,
            label: `Выше среднего на +${comparisonDelta.toFixed(1)}`,
            className: 'bg-green-500/10 text-green-700 dark:text-green-300 border-green-500/20',
          }
        : comparisonDelta < 0
          ? {
              icon: TrendingDown,
              label: `Ниже среднего на ${comparisonDelta.toFixed(1)}`,
              className: 'bg-red-500/10 text-red-700 dark:text-red-300 border-red-500/20',
            }
          : {
              icon: Sparkles,
              label: 'На уровне среднего по группе',
              className: 'bg-muted text-foreground border-border/60',
            };
  const AverageStatusIcon = averageStatus?.icon;

  return (
    <MetricCard className="relative" interactive={false} tint={tone}>
      <div className="space-y-6 p-6">
        <div className="flex items-start gap-4">
          <Button variant="ghost" size="icon" onClick={onBack} className="mt-0.5 shrink-0 rounded-full">
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="min-w-0 flex-1 space-y-3">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{studentName}</h1>
                  {data.rank_in_group && data.total_in_group && (
                    <Badge variant="secondary" className="rounded-full px-3 py-1 text-xs font-medium">
                      #{data.rank_in_group} из {data.total_in_group}
                    </Badge>
                  )}
                </div>
                <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                  <span>Группа {formatGroupCode(data.group_code)}</span>
                  <span className="hidden sm:inline">•</span>
                  <span>{attestationLabel}</span>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline" className={`rounded-full border px-3 py-1 text-xs font-medium ${statusConfig.className}`}>
                  <StatusIcon className="mr-1.5 h-3.5 w-3.5" />
                  {statusConfig.label}
                </Badge>
                {averageStatus && (
                  <Badge variant="outline" className={`rounded-full border px-3 py-1 text-xs font-medium ${averageStatus.className}`}>
                    {AverageStatusIcon && <AverageStatusIcon className="mr-1.5 h-3.5 w-3.5" />}
                    {averageStatus.label}
                  </Badge>
                )}
              </div>
            </div>

            <div className="grid gap-4 lg:grid-cols-[minmax(0,1.3fr)_minmax(240px,0.7fr)]">
              <div className="space-y-3 rounded-3xl border border-border/60 bg-muted/20 p-5">
                <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                  Общая оценка ситуации
                </p>
                <div className="space-y-1">
                  <p className="text-xl font-semibold text-foreground">{statusConfig.label}</p>
                  <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
                    {statusConfig.message}
                  </p>
                </div>
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  <MiniFact label="Порог зачёта" value={minPassing.toFixed(1)} />
                  <MiniFact label="Максимум" value={maxPoints.toFixed(1)} />
                  {groupAverage !== undefined && (
                    <MiniFact label="Среднее по группе" value={groupAverage.toFixed(1)} />
                  )}
                </div>
              </div>

              <div className="rounded-3xl border border-border/60 bg-background/80 p-5">
                <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                  Итоговый балл
                </p>
                <div className="mt-3 flex items-end gap-3">
                  <div className="text-5xl font-semibold tracking-tight text-foreground">
                    <NumberTicker value={totalScore} decimalPlaces={1} delay={0.15} />
                  </div>
                  <div className="pb-1 text-sm text-muted-foreground">/ {maxPoints.toFixed(1)}</div>
                </div>
                <div className="mt-4 flex flex-wrap items-center gap-2">
                  <GradeBadge grade={data.grade} isPassing={isPassing} isEarlySemester={isEarlySemester} />
                  {isExcellent && !isEarlySemester && (
                    <Badge className="rounded-full bg-yellow-500/10 px-3 py-1 text-yellow-700 hover:bg-yellow-500/20 dark:text-yellow-300">
                      <Award className="mr-1.5 h-3.5 w-3.5" />
                      Сильный результат
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between gap-3 text-xs text-muted-foreground">
            <span>0</span>
            <span>Порог: {minPassing.toFixed(1)}</span>
            <span>{maxPoints.toFixed(1)}</span>
          </div>
          <div className="relative">
            <Progress value={progressPercent} className={`h-3 rounded-full ${statusConfig.progressClassName}`} />
            <div
              className="absolute inset-y-0 w-0.5 bg-yellow-500"
              style={{ left: `${(minPassing / Math.max(maxPoints, 1)) * 100}%` }}
            />
          </div>
        </div>
      </div>
      {isExcellent && !isEarlySemester && (
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

function GradeBadge({
  grade,
  isPassing,
  isEarlySemester,
}: {
  grade?: string;
  isPassing?: boolean;
  isEarlySemester?: boolean;
}) {
  if (!grade) {
    return (
      <Badge variant="secondary" className="rounded-full px-3 py-1.5 text-sm">
        Итог пока не выставлен
      </Badge>
    );
  }

  if (isEarlySemester) {
    return (
      <Badge variant="secondary" className="rounded-full px-3 py-1.5 text-sm">
        Итог: {grade}
      </Badge>
    );
  }

  return (
    <Badge
      variant={isPassing ? 'default' : 'destructive'}
      className="rounded-full px-3 py-1.5 text-sm font-medium"
    >
      Итог: {grade}
    </Badge>
  );
}
