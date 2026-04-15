'use client';

import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { AttendanceDistribution, AttendanceStats } from '@/lib/api/types/reports';
import type { ReportSubgroupFilter } from './reportFilters';
import { getAttendanceTrendForSubgroup } from './reportFilters';
import { ChartTooltipCard } from './ChartTooltipCard';

interface AttendanceChartProps {
  distribution: AttendanceDistribution;
  stats?: AttendanceStats;
  selectedSubgroup: ReportSubgroupFilter;
}

interface AttendanceTrendProps {
  stats?: AttendanceStats;
  selectedSubgroup: ReportSubgroupFilter;
}

const COLORS = {
  present: 'hsl(142 72% 29%)',
  late: 'hsl(38 92% 50%)',
  excused: 'hsl(217 91% 60%)',
  absent: 'hsl(0 72% 51%)',
  empty: 'hsl(var(--muted-foreground))',
};

const LABELS: Record<keyof AttendanceDistribution, string> = {
  present: 'Присутствовал',
  late: 'Опоздал',
  excused: 'Уважительная причина',
  absent: 'Отсутствовал',
};

export function AttendanceChart({ distribution, selectedSubgroup }: AttendanceChartProps) {
  const total = distribution.present + distribution.late + distribution.excused + distribution.absent;
  const attendanceRate = total === 0
    ? 0
    : Math.round(((distribution.present + distribution.late * 0.5 + distribution.excused * 0.5) / total) * 100);

  const chartData = total === 0
    ? [{ key: 'empty', label: 'Нет данных', value: 1 }]
    : (Object.entries(distribution) as Array<[keyof AttendanceDistribution, number]>)
      .filter(([, value]) => value > 0)
      .map(([key, value]) => ({
        key,
        label: LABELS[key],
        value,
      }));

  return (
    <Card className="h-full border-border/60 shadow-sm">
      <CardHeader className="space-y-3 pb-1">
        <div className="flex items-center justify-between gap-3">
          <div>
            <CardTitle className="text-base">Посещаемость за период</CardTitle>
            <p className="text-sm text-muted-foreground">
              Итог по выбранной аттестации
            </p>
          </div>
          <Badge variant="outline">{selectedSubgroup === 'all' ? 'Вся группа' : `${selectedSubgroup} подгруппа`}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="relative h-[220px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                dataKey="value"
                innerRadius={62}
                outerRadius={88}
                paddingAngle={2}
                stroke="transparent"
              >
                {chartData.map((item) => (
                  <Cell key={item.key} fill={COLORS[item.key as keyof typeof COLORS] ?? COLORS.empty} />
                ))}
              </Pie>
              {total > 0 && (
                <Tooltip
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) {
                      return null;
                    }

                    const item = payload[0];
                    return (
                      <ChartTooltipCard
                        title={String(item.name ?? 'Посещаемость')}
                        value={`${item.value ?? 0}`}
                      />
                    );
                  }}
                />
              )}
            </PieChart>
          </ResponsiveContainer>

          <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <p className="text-4xl font-semibold tracking-tight">{attendanceRate}%</p>
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-muted-foreground">
          Средняя посещаемость за выбранный период
        </p>

        <div className="grid gap-2 sm:grid-cols-2">
          {chartData.map((item) => (
            <div key={item.key} className="flex items-center justify-between rounded-2xl border border-border/60 bg-background/80 px-3 py-2">
              <div className="flex items-center gap-2">
                <span
                  className="h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: COLORS[item.key as keyof typeof COLORS] ?? COLORS.empty }}
                />
                <span className="text-sm text-muted-foreground">{item.label}</span>
              </div>
              <span className="text-sm font-medium text-foreground">{total > 0 ? item.value : '—'}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export function AttendanceTrend({ stats, selectedSubgroup }: AttendanceTrendProps) {
  const trendData = getAttendanceTrendForSubgroup(stats, selectedSubgroup).map((item) => ({
    date: new Date(item.date).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' }),
    rate: item.rate,
  }));

  return (
    <Card className="border-border/60 shadow-sm">
      <CardHeader className="space-y-3 pb-1">
        <div className="flex items-center justify-between gap-3">
          <div>
            <CardTitle className="text-base">Динамика посещаемости</CardTitle>
            <p className="text-sm text-muted-foreground">
              По занятиям за выбранный период
            </p>
          </div>
          <Badge variant="outline">{selectedSubgroup === 'all' ? 'Вся группа' : `${selectedSubgroup} подгруппа`}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        {trendData.length === 0 ? (
          <div className="flex h-[280px] items-center justify-center rounded-2xl border border-dashed border-border/60 text-sm text-muted-foreground">
            Нет данных о занятиях за выбранный срез
          </div>
        ) : (
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData} margin={{ left: -18, right: 8 }}>
                <defs>
                  <linearGradient id="attendance-area" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.32} />
                    <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="date"
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
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (!active || !payload?.length) {
                      return null;
                    }

                    return (
                      <ChartTooltipCard
                        title={`Занятие ${String(label)}`}
                        value={`${payload[0].value ?? 0}%`}
                        description="Посещаемость на конкретном занятии"
                      />
                    );
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="rate"
                  stroke="hsl(var(--primary))"
                  strokeWidth={2.5}
                  fill="url(#attendance-area)"
                  fillOpacity={1}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
