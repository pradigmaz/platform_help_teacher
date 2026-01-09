'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LabProgress } from '@/lib/api';

interface LabProgressChartProps {
  progress: LabProgress[];
}

function getBarColor(rate: number): string {
  if (rate >= 80) return '#22c55e';  // green-500
  if (rate >= 50) return '#f59e0b';  // amber-500
  return '#ef4444';                   // red-500
}

export function LabProgressChart({ progress }: LabProgressChartProps) {
  if (!progress || progress.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Прогресс сдачи лабораторных</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">
            Нет данных о лабораторных работах
          </p>
        </CardContent>
      </Card>
    );
  }

  const data = progress.map((lab, index) => ({
    name: lab.lab_name.length > 15 ? `Лаб. ${index + 1}` : lab.lab_name,
    fullName: lab.lab_name,
    completed: lab.completed_count,
    total: lab.total_students,
    rate: Math.round(lab.completion_rate),
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Прогресс сдачи лабораторных</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical" margin={{ left: 20, right: 30 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
              <XAxis 
                type="number" 
                domain={[0, 100]} 
                tickFormatter={(v) => `${v}%`}
                tick={{ fontSize: 12 }}
              />
              <YAxis 
                type="category" 
                dataKey="name" 
                width={80}
                tick={{ fontSize: 12 }}
              />
              <Tooltip 
                formatter={(value, _name, props) => {
                  const item = (props as { payload: { completed: number; total: number; fullName: string } }).payload;
                  return [`${item.completed}/${item.total} студентов (${value ?? 0}%)`, item.fullName];
                }}
                contentStyle={{ 
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                }}
              />
              <Bar dataKey="rate" radius={[0, 4, 4, 0]}>
                {data.map((entry, index) => (
                  <Cell key={index} fill={getBarColor(entry.rate)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="flex justify-center gap-4 mt-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-green-500" />
            <span>≥80%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-amber-500" />
            <span>50-79%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-red-500" />
            <span>&lt;50%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
