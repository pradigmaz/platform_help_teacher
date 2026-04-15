'use client';

import { Badge } from '@/components/ui/badge';
import { MetricCard } from '@/components/ui/metric-card';
import { NumberTicker } from '@/components/ui/number-ticker';
import { StudentDetailData } from '@/lib/api';
import { CalendarCheck, FlaskConical, Sparkles } from 'lucide-react';
import type { ReactNode } from 'react';

interface ScoreBreakdownProps {
  data: StudentDetailData;
}

export function ScoreBreakdown({ data }: ScoreBreakdownProps) {
  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
          Из чего складывается результат
        </p>
        <h2 className="text-xl font-semibold tracking-tight">Компоненты оценки</h2>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {data.lab_score !== undefined && (
          <ComponentCard
            tint="blue"
            icon={<FlaskConical className="h-5 w-5" />}
            title="Лабораторные"
            score={data.lab_score}
            summary={getLabSummary(data.labs_completed, data.labs_total)}
          />
        )}

        {data.attendance_score !== undefined && (
          <ComponentCard
            tint="green"
            icon={<CalendarCheck className="h-5 w-5" />}
            title="Посещаемость"
            score={data.attendance_score}
            summary={
              data.attendance_rate !== undefined
                ? `${Math.round(data.attendance_rate)}% занятий за выбранный период`
                : 'Данные по посещаемости доступны внизу страницы'
            }
          />
        )}

        {data.activity_score !== undefined && (
          <ComponentCard
            tint="purple"
            icon={<Sparkles className="h-5 w-5" />}
            title="Активность"
            score={data.activity_score}
            summary={
              data.total_activity_points !== undefined
                ? `${data.total_activity_points} баллов набрано за активность`
                : 'Дополнительный вклад в итоговый результат'
            }
          />
        )}
      </div>
    </div>
  );
}

function getLabSummary(completed?: number, total?: number) {
  if (typeof completed === 'number' && typeof total === 'number') {
    return `Сдано ${completed} из ${total} лабораторных`;
  }

  return 'Вклад лабораторных в итоговый результат';
}

interface ComponentCardProps {
  tint: 'blue' | 'green' | 'purple';
  icon: ReactNode;
  title: string;
  score: number;
  summary: string;
}

function ComponentCard({ tint, icon, title, score, summary }: ComponentCardProps) {
  return (
    <MetricCard tint={tint}>
      <div className="space-y-4 p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-border/60 bg-background/80 text-foreground">
            {icon}
          </div>
          <div className="text-right">
            <p className="text-3xl font-semibold tracking-tight text-foreground">
              <NumberTicker value={score} decimalPlaces={1} delay={0.25} />
            </p>
            <p className="text-xs text-muted-foreground">баллов</p>
          </div>
        </div>

        <div className="space-y-2">
          <p className="text-base font-semibold text-foreground">{title}</p>
          <p className="text-sm leading-relaxed text-muted-foreground">{summary}</p>
        </div>

        <Badge variant="outline" className="rounded-full border-border/60 bg-background/70 px-2.5 py-1 text-xs">
          Компонент итоговой оценки
        </Badge>
      </div>
    </MetricCard>
  );
}
