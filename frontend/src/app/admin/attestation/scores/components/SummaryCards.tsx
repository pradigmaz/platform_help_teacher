'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Users, CheckCircle2, XCircle, TrendingUp, ArrowDown, ArrowUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion } from 'motion/react';

interface AttestationSummary {
  totalStudents: number;
  passedCount: number;
  failedCount: number;
  averageScore: number;
  minScore: number;
  maxScore: number;
  maxPoints: number;
  minPassingPoints: number;
  gradeDistribution: Record<string, number>;
}

interface SummaryCardsProps {
  summary: AttestationSummary;
}

export function AttestationSummaryCards({ summary }: SummaryCardsProps) {
  const passRate = summary.totalStudents > 0 
    ? Math.round((summary.passedCount / summary.totalStudents) * 100) 
    : 0;

  return (
    <div className="space-y-4">
      {/* 4 Main Cards */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={<Users className="h-5 w-5" />}
          label="Всего студентов"
          value={summary.totalStudents}
          description="в выборке"
          color="default"
        />
        <StatCard
          icon={<CheckCircle2 className="h-5 w-5" />}
          label="Зачёт"
          value={summary.passedCount}
          description={`${passRate}% (≥${summary.minPassingPoints} б.)`}
          color="success"
        />
        <StatCard
          icon={<XCircle className="h-5 w-5" />}
          label="Незачёт"
          value={summary.failedCount}
          description={`${100 - passRate}%`}
          color="destructive"
        />
        <StatCard
          icon={<TrendingUp className="h-5 w-5" />}
          label="Средний балл"
          value={summary.averageScore.toFixed(1)}
          description={`из ${summary.maxPoints}`}
          color="primary"
        />
      </div>

      {/* Min/Max + Progress Bar */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            {/* Min */}
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-500/10">
                <ArrowDown className="h-4 w-4 text-red-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Минимум</p>
                <p className="text-lg font-semibold">{summary.minScore}</p>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="flex-1 space-y-2">
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>0</span>
                <span className="font-medium text-foreground">
                  Средний: {summary.averageScore.toFixed(1)}
                </span>
                <span>{summary.maxPoints}</span>
              </div>
              <div className="relative h-3 bg-secondary rounded-full overflow-hidden">
                {/* Passing threshold marker */}
                <div 
                  className="absolute top-0 bottom-0 w-0.5 bg-yellow-500 z-10"
                  style={{ left: `${(summary.minPassingPoints / summary.maxPoints) * 100}%` }}
                />
                {/* Average score indicator */}
                <Progress 
                  value={(summary.averageScore / summary.maxPoints) * 100} 
                  className="h-full"
                />
              </div>
              <p className="text-xs text-center text-muted-foreground">
                Порог зачёта: {summary.minPassingPoints} баллов
              </p>
            </div>

            {/* Max */}
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-green-500/10">
                <ArrowUp className="h-4 w-4 text-green-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Максимум</p>
                <p className="text-lg font-semibold">{summary.maxScore}</p>
              </div>
            </div>
          </div>

          {/* Grade Distribution */}
          {Object.keys(summary.gradeDistribution).length > 0 && (
            <div className="mt-4 pt-4 border-t">
              <p className="text-xs text-muted-foreground mb-2">Распределение оценок</p>
              <div className="flex gap-2">
                {Object.entries(summary.gradeDistribution).map(([grade, count]) => (
                  <div 
                    key={grade} 
                    className={cn(
                      "flex-1 text-center py-2 rounded-lg text-sm font-medium",
                      grade === 'отл' && "bg-green-500/10 text-green-600",
                      grade === 'хор' && "bg-blue-500/10 text-blue-600",
                      grade === 'уд' && "bg-yellow-500/10 text-yellow-600",
                      grade === 'неуд' && "bg-red-500/10 text-red-600",
                    )}
                  >
                    <div className="text-lg font-bold">{count}</div>
                    <div className="text-xs opacity-80">{grade}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: number | string;
  description: string;
  color: 'default' | 'success' | 'destructive' | 'primary';
}

function StatCard({ icon, label, value, description, color }: StatCardProps) {
  const colorClasses = {
    default: 'text-foreground bg-muted',
    success: 'text-green-500 bg-green-500/10',
    destructive: 'text-red-500 bg-red-500/10',
    primary: 'text-blue-500 bg-blue-500/10',
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.2 }}
    >
      <Card>
        <CardContent className="p-4">
          <div className={cn("p-2 rounded-lg w-fit mb-2", colorClasses[color])}>
            {icon}
          </div>
          <p className="text-2xl font-bold">{value}</p>
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className="text-xs text-muted-foreground/70 mt-1">{description}</p>
        </CardContent>
      </Card>
    </motion.div>
  );
}
