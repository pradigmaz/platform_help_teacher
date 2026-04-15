'use client';

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { LabProgress } from '@/lib/api';
import type { ReportSubgroupFilter } from './reportFilters';
import { ChartTooltipCard } from './ChartTooltipCard';

interface LabProgressChartProps {
  progress: LabProgress[];
  selectedSubgroup: ReportSubgroupFilter;
}

function getBarColor(rate: number) {
  if (rate >= 80) {
    return 'hsl(142 72% 29%)';
  }

  if (rate >= 50) {
    return 'hsl(38 92% 50%)';
  }

  return 'hsl(0 72% 51%)';
}

export function LabProgressChart({ progress, selectedSubgroup }: LabProgressChartProps) {
  const hasData = progress.length > 0;
  const chartData = hasData
    ? progress.map((lab, index) => ({
      name: `Л${index + 1}`,
      fullName: lab.lab_name,
      completed: lab.completed_count,
      total: lab.total_students,
      rate: Math.round(lab.completion_rate),
    }))
    : Array.from({ length: 8 }, (_, index) => ({
      name: `Л${index + 1}`,
      fullName: `Лабораторная ${index + 1}`,
      completed: 0,
      total: 0,
      rate: 0,
    }));

  return (
    <Card className="h-full border-border/60 shadow-sm">
      <CardHeader className="space-y-3 pb-1">
        <div className="flex items-center justify-between gap-3">
          <div>
            <CardTitle className="text-base">Готовность лабораторных</CardTitle>
            <p className="text-sm text-muted-foreground">
              Доля студентов, сдавших каждую работу
            </p>
          </div>
          <Badge variant="outline">{selectedSubgroup === 'all' ? 'Вся группа' : `${selectedSubgroup} подгруппа`}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="h-[260px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ left: -18, right: 8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 11 }}
                stroke="hsl(var(--muted-foreground))"
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                domain={[0, 100]}
                width={38}
                tick={{ fontSize: 11 }}
                tickFormatter={(value) => `${value}%`}
                stroke="hsl(var(--muted-foreground))"
                axisLine={false}
                tickLine={false}
              />
              {hasData && (
                <Tooltip
                  cursor={{ fill: 'hsl(var(--accent) / 0.24)' }}
                  content={({ active, payload, label }) => {
                    if (!active || !payload?.length) {
                      return null;
                    }

                    const item = payload[0].payload as {
                      completed: number;
                      total: number;
                      fullName: string;
                      rate: number;
                    };

                    return (
                      <ChartTooltipCard
                        title={`${String(label)} · ${item.fullName}`}
                        value={`${item.completed}/${item.total} (${item.rate}%)`}
                        description="Сколько студентов сдали эту лабораторную"
                      />
                    );
                  }}
                />
              )}
              <Bar dataKey="rate" radius={[10, 10, 0, 0]}>
                {chartData.map((item, index) => (
                  <Cell key={index} fill={hasData && item.rate > 0 ? getBarColor(item.rate) : 'hsl(var(--muted))'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="grid gap-2 sm:grid-cols-3">
          <LegendItem color="hsl(142 72% 29%)" label="Высокая готовность" description="80% и выше" />
          <LegendItem color="hsl(38 92% 50%)" label="Средняя готовность" description="50–79%" />
          <LegendItem color="hsl(0 72% 51%)" label="Низкая готовность" description="Ниже 50%" />
        </div>
      </CardContent>
    </Card>
  );
}

function LegendItem({ color, label, description }: { color: string; label: string; description: string }) {
  return (
    <div className="rounded-2xl border border-border/60 bg-background/80 px-3 py-2">
      <div className="flex items-center gap-2">
        <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
        <span className="text-sm font-medium">{label}</span>
      </div>
      <p className="mt-1 text-xs text-muted-foreground">{description}</p>
    </div>
  );
}
