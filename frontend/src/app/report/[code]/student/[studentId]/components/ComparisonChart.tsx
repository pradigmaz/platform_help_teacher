'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';
import { StudentDetailData } from '@/lib/api';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Cell,
  LabelList,
} from 'recharts';

interface ComparisonChartProps {
  data: StudentDetailData;
}

export function ComparisonChart({ data }: ComparisonChartProps) {
  const groupAvg = data.group_average_score;
  const studentScore = data.total_score || 0;
  
  if (groupAvg === undefined) return null;

  const diff = studentScore - groupAvg;
  const diffPercent = groupAvg > 0 ? ((diff / groupAvg) * 100).toFixed(1) : '0';
  
  const chartData = [
    {
      name: 'Вы',
      value: studentScore,
      fill: studentScore >= groupAvg ? '#22c55e' : '#ef4444',
    },
    {
      name: 'Среднее',
      value: groupAvg,
      fill: '#6b7280',
    },
  ];

  const maxValue = Math.max(studentScore, groupAvg, data.max_points || 40);

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Сравнение с группой</CardTitle>
          <div className={cn(
            "flex items-center gap-1 text-sm font-medium",
            diff > 0 && "text-green-600 dark:text-green-400",
            diff < 0 && "text-red-600 dark:text-red-400",
            diff === 0 && "text-muted-foreground"
          )}>
            {diff > 0 ? (
              <>
                <TrendingUp className="h-4 w-4" />
                +{diff.toFixed(1)} ({diffPercent}%)
              </>
            ) : diff < 0 ? (
              <>
                <TrendingDown className="h-4 w-4" />
                {diff.toFixed(1)} ({diffPercent}%)
              </>
            ) : (
              <>
                <Minus className="h-4 w-4" />
                На уровне среднего
              </>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-24">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 5, right: 40, left: 60, bottom: 5 }}
            >
              <XAxis 
                type="number" 
                domain={[0, maxValue]} 
                hide 
              />
              <YAxis 
                type="category" 
                dataKey="name" 
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 12 }}
              />
              <Bar 
                dataKey="value" 
                radius={[0, 4, 4, 0]}
                barSize={24}
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
                <LabelList 
                  dataKey="value" 
                  position="right" 
                  formatter={(value) => typeof value === 'number' ? value.toFixed(1) : String(value)}
                  style={{ fontSize: 12, fontWeight: 600 }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        
        {/* Legend */}
        <div className="flex justify-center gap-6 mt-2 text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <div className={cn(
              "w-3 h-3 rounded-sm",
              studentScore >= groupAvg ? "bg-green-500" : "bg-red-500"
            )} />
            <span>Ваш балл</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-sm bg-gray-500" />
            <span>Среднее по группе</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
