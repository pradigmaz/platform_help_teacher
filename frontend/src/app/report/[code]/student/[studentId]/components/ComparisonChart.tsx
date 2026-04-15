'use client';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { StudentDetailData } from '@/lib/api';
import { Minus, TrendingDown, TrendingUp, Users } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ComparisonChartProps {
  data: StudentDetailData;
}

export function ComparisonChart({ data }: ComparisonChartProps) {
  const groupAverage = data.group_average_score;
  const studentScore = data.total_score || 0;
  const maxPoints = data.max_points || 35;
  const minPassingPoints = data.min_passing_points || 20;

  if (groupAverage === undefined) {
    return null;
  }

  const difference = studentScore - groupAverage;
  const comparisonTone = difference > 0 ? 'green' : difference < 0 ? 'red' : 'neutral';
  const ComparisonIcon = difference > 0 ? TrendingUp : difference < 0 ? TrendingDown : Minus;

  return (
    <Card className="group relative overflow-hidden border-border/60 bg-card/95 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/25 hover:bg-accent/10 hover:shadow-lg focus-within:border-primary/25 focus-within:shadow-lg">
      <div className="pointer-events-none absolute inset-x-6 top-0 h-px bg-gradient-to-r from-transparent via-blue-500/35 to-transparent" />
      <div className="pointer-events-none absolute -right-10 -top-10 h-28 w-28 rounded-full bg-blue-500/15 opacity-0 blur-3xl transition-opacity duration-200 group-hover:opacity-100 group-focus-within:opacity-100" />
      <CardHeader className="space-y-4 border-b border-border/60 bg-muted/20 pb-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5 text-muted-foreground" />
              <CardTitle className="text-lg">Положение в группе</CardTitle>
            </div>
            <p className="text-sm text-muted-foreground">
              Сравнение с порогом зачёта и средним результатом группы.
            </p>
          </div>
          {data.rank_in_group && data.total_in_group && (
            <Badge variant="secondary" className="rounded-full px-3 py-1 text-xs font-medium">
              #{data.rank_in_group} из {data.total_in_group}
            </Badge>
          )}
        </div>

        <div
          className={cn(
            'flex items-center justify-between rounded-2xl border px-4 py-3',
            comparisonTone === 'green' && 'border-green-500/20 bg-green-500/10 text-green-700 dark:text-green-300',
            comparisonTone === 'red' && 'border-red-500/20 bg-red-500/10 text-red-700 dark:text-red-300',
            comparisonTone === 'neutral' && 'border-border/60 bg-background/80 text-foreground',
          )}
        >
          <div>
            <p className="text-xs uppercase tracking-[0.16em] opacity-70">Относительно среднего</p>
            <p className="mt-1 text-2xl font-semibold">
              {difference > 0 ? '+' : ''}
              {difference.toFixed(1)}
            </p>
          </div>
          <ComparisonIcon className="h-8 w-8" />
        </div>
      </CardHeader>

      <CardContent className="space-y-5 p-6">
        <ComparisonRow
          label="Ваш результат"
          value={studentScore}
          maxValue={maxPoints}
          colorClassName="[&>div]:bg-foreground"
          helperText="Текущий итоговый балл"
        />
        <ComparisonRow
          label="Средний балл группы"
          value={groupAverage}
          maxValue={maxPoints}
          colorClassName="[&>div]:bg-blue-500"
          helperText="Ориентир по группе"
        />
        <ComparisonRow
          label="Порог зачёта"
          value={minPassingPoints}
          maxValue={maxPoints}
          colorClassName="[&>div]:bg-yellow-500"
          helperText="Минимум для зачёта"
        />
      </CardContent>
    </Card>
  );
}

interface ComparisonRowProps {
  label: string;
  value: number;
  maxValue: number;
  colorClassName: string;
  helperText: string;
}

function ComparisonRow({
  label,
  value,
  maxValue,
  colorClassName,
  helperText,
}: ComparisonRowProps) {
  const percent = Math.min((value / Math.max(maxValue, 1)) * 100, 100);

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <p className="text-sm font-medium text-foreground">{label}</p>
          <p className="text-xs text-muted-foreground">{helperText}</p>
        </div>
        <div className="text-right">
          <p className="text-lg font-semibold text-foreground">{value.toFixed(1)}</p>
          <p className="text-xs text-muted-foreground">из {maxValue.toFixed(1)}</p>
        </div>
      </div>
      <Progress value={percent} className={cn('h-2.5 rounded-full', colorClassName)} />
    </div>
  );
}
