'use client';

import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LabProgress } from '@/lib/api';

interface LabProgressChartProps {
  progress: LabProgress[];
  progressBySubgroup?: Record<string, LabProgress[]>;
  hasSubgroups?: boolean;
}

function getBarColor(rate: number): string {
  if (rate >= 80) return '#22c55e';  // green-500
  if (rate >= 50) return '#f59e0b';  // amber-500
  return '#ef4444';                   // red-500
}

export function LabProgressChart({ progress, progressBySubgroup, hasSubgroups }: LabProgressChartProps) {
  const [selectedTab, setSelectedTab] = useState<string>('all');
  
  // Выбираем данные в зависимости от таба
  const currentProgress = selectedTab === 'all' 
    ? progress 
    : progressBySubgroup?.[selectedTab] || progress;
  
  const hasData = currentProgress && currentProgress.length > 0;

  // Пустые данные - показываем реальное количество лаб или 8 по умолчанию
  const defaultLabCount = 8;
  const emptyData = Array.from({ length: defaultLabCount }, (_, i) => ({
    name: `Л${i + 1}`,
    rate: 0,
  }));

  // TODO: фильтрация по подгруппам когда бэкенд поддержит
  const data = hasData 
    ? currentProgress.map((lab, index) => ({
        name: `Л${index + 1}`,
        fullName: lab.lab_name,
        completed: lab.completed_count,
        total: lab.total_students,
        rate: Math.round(lab.completion_rate),
      }))
    : emptyData;

  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Прогресс сдачи лабораторных</CardTitle>
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
        <div className="h-[220px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ left: -10, right: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="hsl(var(--border))" />
              <XAxis 
                dataKey="name" 
                tick={{ fontSize: 11 }}
                stroke="hsl(var(--muted-foreground))"
                axisLine={false}
                tickLine={false}
              />
              <YAxis 
                domain={[0, 100]} 
                tickFormatter={(v) => `${v}%`}
                tick={{ fontSize: 11 }}
                stroke="hsl(var(--muted-foreground))"
                axisLine={false}
                tickLine={false}
                width={35}
              />
              {hasData && (
                <Tooltip 
                  formatter={(value, _name, props) => {
                    const item = (props as { payload: { completed: number; total: number; fullName: string } }).payload;
                    return [`${item.completed}/${item.total} (${value}%)`, item.fullName];
                  }}
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
              )}
              <Bar dataKey="rate" radius={[4, 4, 0, 0]}>
                {data.map((entry, index) => (
                  <Cell key={index} fill={hasData && entry.rate > 0 ? getBarColor(entry.rate) : '#3f3f46'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="flex justify-center gap-4 mt-2 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <div className="w-2.5 h-2.5 rounded bg-green-500" />
            <span>≥80%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2.5 h-2.5 rounded bg-amber-500" />
            <span>50-79%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2.5 h-2.5 rounded bg-red-500" />
            <span>&lt;50%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
