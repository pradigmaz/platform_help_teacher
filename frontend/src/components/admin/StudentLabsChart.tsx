'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Calendar } from 'lucide-react';

interface LabsStatusData {
  name: string;
  value: number;
  color: string;
  [key: string]: string | number;
}

interface StudentLabsChartProps {
  data: LabsStatusData[];
}

export default function StudentLabsChart({ data }: StudentLabsChartProps) {
  // Фильтруем только для отображения в графике (нули не показываем в pie)
  const chartData = data.filter(d => d.value > 0);
  const hasData = chartData.length > 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Calendar className="w-5 h-5" />
          Статус лабораторных
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64 flex items-center justify-center">
          {hasData ? (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, value }) => `${name ?? ''}: ${value}`}
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center text-muted-foreground">
              <Calendar className="w-12 h-12 mx-auto mb-2 opacity-20" />
              <p>Нет данных о сдачах</p>
            </div>
          )}
        </div>
        <div className="flex flex-wrap justify-center gap-3 mt-4">
          {data.map((item) => (
            <div key={item.name} className="flex items-center gap-1 text-sm">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
              <span className={item.value === 0 ? 'text-muted-foreground' : ''}>
                {item.name}: {item.value}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

