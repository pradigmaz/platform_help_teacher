'use client';

import { useState } from 'react';
import { 
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  AreaChart, Area, XAxis, YAxis, CartesianGrid
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AttendanceDistribution, AttendanceStats } from '@/lib/api/types/reports';

const COLORS: Record<string, string> = {
  present: '#22c55e',
  late: '#f59e0b',
  excused: '#3b82f6',
  absent: '#ef4444',
  empty: '#3f3f46',
};

const LABELS: Record<string, string> = {
  present: 'Присутствовал',
  late: 'Опоздал',
  excused: 'Уважительная',
  absent: 'Отсутствовал',
};

function getChartData(dist: AttendanceDistribution) {
  return [
    { name: LABELS.present, value: dist.present, key: 'present' },
    { name: LABELS.late, value: dist.late, key: 'late' },
    { name: LABELS.excused, value: dist.excused, key: 'excused' },
    { name: LABELS.absent, value: dist.absent, key: 'absent' },
  ].filter(item => item.value > 0);
}

function getTotal(dist: AttendanceDistribution) {
  return dist.present + dist.late + dist.excused + dist.absent;
}

function getRate(dist: AttendanceDistribution) {
  const total = getTotal(dist);
  if (total === 0) return 0;
  return Math.round((dist.present + dist.late * 0.5 + dist.excused * 0.5) / total * 100);
}

interface AttendanceDonutProps {
  distribution: AttendanceDistribution;
  stats?: AttendanceStats;
  hasSubgroups?: boolean;
}

// Donut chart - только pie с процентом
export function AttendanceDonut({ distribution, stats, hasSubgroups }: AttendanceDonutProps) {
  const [selectedTab, setSelectedTab] = useState<string>('all');
  
  const currentDist = selectedTab === 'all' 
    ? distribution 
    : stats?.by_subgroup?.[selectedTab] || distribution;
  
  const data = getChartData(currentDist);
  const total = getTotal(currentDist);
  const attendanceRate = getRate(currentDist);
  const chartData = total === 0 ? [{ name: 'Нет данных', value: 1, key: 'empty' }] : data;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Посещаемость за период</CardTitle>
          {hasSubgroups && (
            <Tabs value={selectedTab} onValueChange={setSelectedTab}>
              <TabsList className="h-8">
                <TabsTrigger value="all" className="text-xs px-2 h-6">Все</TabsTrigger>
                <TabsTrigger value="1" className="text-xs px-2 h-6">1 п/г</TabsTrigger>
                <TabsTrigger value="2" className="text-xs px-2 h-6">2 п/г</TabsTrigger>
              </TabsList>
            </Tabs>
          )}
        </div>
      </CardHeader>
      <CardContent>
          <div className="h-[180px] relative">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={60}
                paddingAngle={total === 0 ? 0 : 2}
                dataKey="value"
              >
                {chartData.map((entry) => (
                  <Cell key={entry.key} fill={COLORS[entry.key] || COLORS.empty} />
                ))}
              </Pie>
              {total > 0 && (
                <Tooltip 
                  formatter={(value) => [`${value}`, '']}
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
              )}
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="text-center">
              <div className="text-2xl font-bold">{attendanceRate}%</div>
              <div className="text-xs text-muted-foreground">за период</div>
            </div>
          </div>
        </div>
        {/* Легенда */}
        <div className="flex flex-wrap gap-3 mt-2 justify-center">
          {(total > 0 ? data : [{ key: 'empty', name: 'Нет данных', value: 0 }]).map((item) => (
            <div key={item.key} className="flex items-center gap-1.5">
              <div 
                className="w-2.5 h-2.5 rounded-full" 
                style={{ backgroundColor: COLORS[item.key] }}
              />
              <span className="text-xs text-muted-foreground">
                {item.name}{total > 0 ? `: ${item.value}` : ''}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

interface AttendanceTrendProps {
  stats?: AttendanceStats;
  hasSubgroups?: boolean;
}

// Trend chart - AreaChart на всю ширину
export function AttendanceTrend({ stats, hasSubgroups }: AttendanceTrendProps) {
  const [selectedTab, setSelectedTab] = useState<string>('all');

  // Фильтруем данные по подгруппе
  // Если hasSubgroups=false: "all" показывает ВСЕ занятия (группа без подгрупп)
  // Если hasSubgroups=true: "all" = только лекции (subgroup === null)
  // "1" или "2" = лабы соответствующей подгруппы
  const trendData = stats?.trend
    ?.filter(t => {
      if (selectedTab === 'all') {
        // Группа без подгрупп - показываем всё
        if (!hasSubgroups) return true;
        // Группа с подгруппами - только лекции
        return t.subgroup === null || t.subgroup === undefined;
      }
      return t.subgroup?.toString() === selectedTab;
    })
    ?.map(t => ({
      date: new Date(t.date).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' }),
      rate: t.rate
    })) || [];

  const hasData = trendData.length > 0;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Посещаемость по занятиям</CardTitle>
          {hasSubgroups && (
            <Tabs value={selectedTab} onValueChange={setSelectedTab}>
              <TabsList className="h-8">
                <TabsTrigger value="all" className="text-xs px-2 h-6">Все</TabsTrigger>
                <TabsTrigger value="1" className="text-xs px-2 h-6">1 п/г</TabsTrigger>
                <TabsTrigger value="2" className="text-xs px-2 h-6">2 п/г</TabsTrigger>
              </TabsList>
            </Tabs>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {!hasData ? (
          <div className="h-[280px] flex items-center justify-center text-muted-foreground">
            Нет данных о занятиях
          </div>
        ) : (
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData} margin={{ left: -10, right: 10 }}>
                <defs>
                  <linearGradient id="colorTrend" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
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
                  tick={{ fontSize: 11 }} 
                  stroke="hsl(var(--muted-foreground))"
                  width={40}
                  tickFormatter={(v) => `${v}%`}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  formatter={(value) => [`${value}%`, 'Занятие']}
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Area 
                  type="monotone" 
                  dataKey="rate" 
                  stroke="#22c55e"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorTrend)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Legacy export для обратной совместимости
interface AttendanceChartProps {
  distribution: AttendanceDistribution;
  stats?: AttendanceStats;
  hasSubgroups?: boolean;
}

export function AttendanceChart({ distribution, stats, hasSubgroups }: AttendanceChartProps) {
  return <AttendanceDonut distribution={distribution} stats={stats} hasSubgroups={hasSubgroups} />;
}
