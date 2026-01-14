'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus, Users } from 'lucide-react';
import { cn } from '@/lib/utils';
import { StudentDetailData } from '@/lib/api';

interface ComparisonChartProps {
  data: StudentDetailData;
}

export function ComparisonChart({ data }: ComparisonChartProps) {
  const groupAvg = data.group_average_score;
  const studentScore = data.total_score || 0;
  const maxPoints = data.max_points || 35;
  
  if (groupAvg === undefined) return null;

  const diff = studentScore - groupAvg;
  
  // Позиция студента на шкале (0-100%)
  const studentPosition = Math.min((studentScore / maxPoints) * 100, 100);
  const avgPosition = Math.min((groupAvg / maxPoints) * 100, 100);

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-lg">Сравнение с группой</CardTitle>
          </div>
          {data.rank_in_group && data.total_in_group && (
            <Badge variant="secondary">
              #{data.rank_in_group} из {data.total_in_group}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Индикатор относительно среднего */}
        <div className="flex items-center justify-between p-4 rounded-lg bg-secondary/50">
          <div>
            <p className="text-sm text-muted-foreground">Относительно среднего</p>
            <p className={cn(
              "text-2xl font-bold",
              diff > 0 && "text-green-600 dark:text-green-400",
              diff < 0 && "text-red-600 dark:text-red-400",
              diff === 0 && "text-muted-foreground"
            )}>
              {diff > 0 ? '+' : ''}{diff.toFixed(1)}
            </p>
          </div>
          {diff > 0 ? (
            <TrendingUp className="h-8 w-8 text-green-500" />
          ) : diff < 0 ? (
            <TrendingDown className="h-8 w-8 text-red-500" />
          ) : (
            <Minus className="h-8 w-8 text-muted-foreground" />
          )}
        </div>

        {/* Визуальная шкала */}
        <div className="space-y-2">
          <div className="relative h-8 rounded-full bg-secondary">
            {/* Маркер среднего значения */}
            <div 
              className="absolute top-0 h-full w-0.5 bg-muted-foreground/50 z-10" 
              style={{ left: `${avgPosition}%` }}
            >
              <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] text-muted-foreground whitespace-nowrap">
                Ср: {groupAvg.toFixed(1)}
              </div>
            </div>
            
            {/* Позиция студента */}
            <div
              className={cn(
                "absolute top-1/2 h-5 w-5 -translate-x-1/2 -translate-y-1/2 rounded-full shadow-lg ring-2 ring-background z-20",
                studentScore >= groupAvg ? "bg-green-500" : "bg-red-500"
              )}
              style={{ left: `${studentPosition}%` }}
            >
              <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-[10px] font-bold whitespace-nowrap">
                {studentScore.toFixed(1)}
              </div>
            </div>
          </div>
          
          {/* Подписи шкалы */}
          <div className="flex justify-between text-xs text-muted-foreground pt-4">
            <span>0</span>
            <span>Средний: {groupAvg.toFixed(1)}</span>
            <span>{maxPoints}</span>
          </div>
        </div>

        {/* Legend */}
        <div className="flex justify-center gap-6 text-xs text-muted-foreground pt-2 border-t">
          <div className="flex items-center gap-1.5">
            <div className={cn(
              "w-3 h-3 rounded-full",
              studentScore >= groupAvg ? "bg-green-500" : "bg-red-500"
            )} />
            <span>Ваш балл</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-0.5 bg-muted-foreground/50" />
            <span>Среднее по группе</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
