'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AttendanceDistribution } from '@/lib/api';

interface AttendanceChartProps {
  distribution: AttendanceDistribution;
}

const COLORS = {
  present: '#22c55e',  // green-500
  late: '#f59e0b',     // amber-500
  excused: '#3b82f6',  // blue-500
  absent: '#ef4444',   // red-500
};

const LABELS: Record<string, string> = {
  present: 'Присутствовал',
  late: 'Опоздал',
  excused: 'Уважительная',
  absent: 'Отсутствовал',
};

export function AttendanceChart({ distribution }: AttendanceChartProps) {
  const data = [
    { name: LABELS.present, value: distribution.present, key: 'present' },
    { name: LABELS.late, value: distribution.late, key: 'late' },
    { name: LABELS.excused, value: distribution.excused, key: 'excused' },
    { name: LABELS.absent, value: distribution.absent, key: 'absent' },
  ].filter(item => item.value > 0);

  const total = distribution.present + distribution.late + distribution.excused + distribution.absent;

  if (total === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Распределение посещаемости</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">
            Нет данных о посещаемости
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Распределение посещаемости</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                paddingAngle={2}
                dataKey="value"
                label={({ name, percent }) => `${name}: ${((percent ?? 0) * 100).toFixed(0)}%`}
                labelLine={false}
              >
                {data.map((entry) => (
                  <Cell 
                    key={entry.key} 
                    fill={COLORS[entry.key as keyof typeof COLORS]} 
                  />
                ))}
              </Pie>
              <Tooltip 
                formatter={(value) => [`${value} занятий`, '']}
                contentStyle={{ 
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                }}
              />
              <Legend 
                verticalAlign="bottom" 
                height={36}
                formatter={(value: string) => <span className="text-sm">{value}</span>}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
