'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  Trophy, 
  FlaskConical, 
  CalendarCheck, 
  Sparkles,
  TrendingUp,
  TrendingDown,
  Award
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { StudentDetailData } from '@/lib/api';
import { NumberTicker } from '@/components/ui/number-ticker';
import { ShineBorder } from '@/components/ui/shine-border';

interface ScoreBreakdownProps {
  data: StudentDetailData;
}

export function ScoreBreakdown({ data }: ScoreBreakdownProps) {
  const maxPoints = data.max_points || 40;
  const minPassing = data.min_passing_points || 18;
  const totalScore = data.total_score || 0;
  const isPassing = data.is_passing ?? totalScore >= minPassing;
  const progressPercent = Math.min((totalScore / maxPoints) * 100, 100);
  const isExcellent = totalScore >= 34; // 85% of 40

  return (
    <div className="space-y-4">
      {/* Hero Score Card */}
      <Card className="relative overflow-hidden">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row md:items-center gap-6">
            {/* Circular Score Indicator */}
            <div className="flex items-center gap-4">
              <div className="relative">
                <div className={cn(
                  "w-24 h-24 rounded-full flex items-center justify-center",
                  "border-4",
                  isPassing ? "border-green-500 bg-green-500/10" : "border-red-500 bg-red-500/10"
                )}>
                  <div className="text-center">
                    <span className="text-3xl font-bold">
                      <NumberTicker value={totalScore} decimalPlaces={1} delay={0.2} />
                    </span>
                    <p className="text-xs text-muted-foreground">/ {maxPoints}</p>
                  </div>
                </div>
                {isExcellent && (
                  <div className="absolute -top-1 -right-1 p-1.5 rounded-full bg-yellow-500 text-white">
                    <Award className="h-4 w-4" />
                  </div>
                )}
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Итоговый балл</p>
                <GradeBadge grade={data.grade} isPassing={isPassing} />
                {isExcellent && (
                  <Badge className="mt-1 bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-200 dark:border-yellow-800">
                    <Award className="h-3 w-3 mr-1" />
                    Отличник
                  </Badge>
                )}
              </div>
            </div>

            {/* Progress Bar */}
            <div className="flex-1 space-y-2">
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>0</span>
                <span className="font-medium">Порог: {minPassing}</span>
                <span>{maxPoints}</span>
              </div>
              <div className="relative h-4 bg-secondary rounded-full overflow-hidden">
                {/* Passing threshold marker */}
                <div 
                  className="absolute top-0 bottom-0 w-0.5 bg-yellow-500 z-10"
                  style={{ left: `${(minPassing / maxPoints) * 100}%` }}
                />
                <Progress 
                  value={progressPercent} 
                  className={cn(
                    "h-full",
                    isPassing ? "[&>div]:bg-green-500" : "[&>div]:bg-red-500"
                  )}
                />
              </div>
              <p className="text-xs text-center">
                {isPassing ? (
                  <span className="text-green-600 dark:text-green-400">✓ Зачёт получен</span>
                ) : (
                  <span className="text-red-600 dark:text-red-400">✗ Зачёт не получен</span>
                )}
              </p>
            </div>
          </div>

          {/* Comparison with group average */}
          {data.group_average_score !== undefined && (
            <div className="mt-4 pt-4 border-t flex flex-wrap items-center gap-2 text-sm">
              {totalScore > data.group_average_score ? (
                <TrendingUp className="h-4 w-4 text-green-500" />
              ) : totalScore < data.group_average_score ? (
                <TrendingDown className="h-4 w-4 text-red-500" />
              ) : (
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              )}
              <span className="text-muted-foreground">Средний балл группы:</span>
              <span className="font-medium">{data.group_average_score.toFixed(1)}</span>
              {totalScore > data.group_average_score ? (
                <Badge variant="outline" className="bg-green-500/10 text-green-600 dark:text-green-400 border-green-200 dark:border-green-800">
                  +{(totalScore - data.group_average_score).toFixed(1)} выше среднего
                </Badge>
              ) : totalScore < data.group_average_score ? (
                <Badge variant="outline" className="bg-red-500/10 text-red-600 dark:text-red-400 border-red-200 dark:border-red-800">
                  {(totalScore - data.group_average_score).toFixed(1)} ниже среднего
                </Badge>
              ) : (
                <Badge variant="outline">на уровне среднего</Badge>
              )}
            </div>
          )}
        </CardContent>
        {isExcellent && (
          <ShineBorder 
            shineColor={["#fbbf24", "#f59e0b", "#d97706"]} 
            borderWidth={2}
            duration={8}
          />
        )}
      </Card>

      {/* Component Breakdown Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        {/* Labs Score */}
        {data.lab_score !== undefined && (
          <ComponentCard
            icon={<FlaskConical className="h-5 w-5" />}
            title="Лабораторные"
            score={data.lab_score}
            color="blue"
            details={data.labs_completed !== undefined && data.labs_total !== undefined ? (
              <span>Сдано: {data.labs_completed} из {data.labs_total}</span>
            ) : undefined}
          />
        )}

        {/* Attendance Score */}
        {data.attendance_score !== undefined && (
          <ComponentCard
            icon={<CalendarCheck className="h-5 w-5" />}
            title="Посещаемость"
            score={data.attendance_score}
            color="emerald"
            details={data.attendance_rate !== undefined ? (
              <span>{Math.round(data.attendance_rate)}% занятий</span>
            ) : undefined}
          />
        )}

        {/* Activity Score */}
        {data.activity_score !== undefined && (
          <ComponentCard
            icon={<Sparkles className="h-5 w-5" />}
            title="Активность"
            score={data.activity_score}
            color="purple"
            details={data.total_activity_points !== undefined ? (
              <span>{data.total_activity_points} баллов активности</span>
            ) : undefined}
          />
        )}
      </div>
    </div>
  );
}

interface ComponentCardProps {
  icon: React.ReactNode;
  title: string;
  score: number;
  color: 'blue' | 'emerald' | 'purple';
  details?: React.ReactNode;
}

function ComponentCard({ icon, title, score, color, details }: ComponentCardProps) {
  const colorClasses = {
    blue: 'bg-blue-500/10 text-blue-500',
    emerald: 'bg-emerald-500/10 text-emerald-500',
    purple: 'bg-purple-500/10 text-purple-500',
  };

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className={cn("p-2 rounded-lg", colorClasses[color])}>
            {icon}
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold">
              <NumberTicker value={score} decimalPlaces={1} delay={0.3} />
            </p>
            <p className="text-xs text-muted-foreground">баллов</p>
          </div>
        </div>
        <p className="mt-2 font-medium">{title}</p>
        {details && (
          <p className="text-xs text-muted-foreground mt-1">{details}</p>
        )}
      </CardContent>
    </Card>
  );
}

function GradeBadge({ grade, isPassing }: { grade?: string; isPassing?: boolean }) {
  if (!grade) return <span className="text-muted-foreground text-lg">—</span>;

  const className = cn(
    "text-lg px-4 py-1",
    grade === 'отл' && 'bg-green-500/10 text-green-600 dark:text-green-400 hover:bg-green-500/20',
    grade === 'хор' && 'bg-blue-500/10 text-blue-600 dark:text-blue-400 hover:bg-blue-500/20',
    grade === 'уд' && 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 hover:bg-yellow-500/20',
    grade === 'неуд' && 'bg-red-500/10 text-red-600 dark:text-red-400 hover:bg-red-500/20',
  );

  return (
    <Badge variant={isPassing ? 'default' : 'destructive'} className={className}>
      {grade}
    </Badge>
  );
}
