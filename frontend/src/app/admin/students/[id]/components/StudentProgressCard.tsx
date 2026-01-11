'use client';

import { TrendingUp, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AnimatedCircularProgress } from '@/components/ui/animated-circular-progress';
import { StudentStats } from './types';

interface Props {
  stats: StudentStats;
}

export function StudentProgressCard({ stats }: Props) {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <TrendingUp className="w-5 h-5" />
          Прогресс
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4 py-4">
          <div className="flex flex-col items-center">
            <AnimatedCircularProgress
              value={stats.points_percent}
              size={100}
              strokeWidth={8}
              gradientFrom="#22c55e"
              gradientTo="#10b981"
              label="Баллы"
            />
            <div className="mt-2 text-center">
              <span className="text-xs text-muted-foreground">
                {stats.points_earned} / {stats.points_max}
              </span>
            </div>
          </div>
          
          <div className="flex flex-col items-center">
            <AnimatedCircularProgress
              value={stats.labs_total > 0 ? (stats.labs_accepted / stats.labs_total) * 100 : 0}
              size={100}
              strokeWidth={8}
              gradientFrom="#3b82f6"
              gradientTo="#06b6d4"
              label="Лабы"
            />
            <div className="mt-2 text-center">
              <span className="text-xs text-muted-foreground">
                {stats.labs_accepted} / {stats.labs_total}
              </span>
            </div>
          </div>
          
          <div className="flex flex-col items-center">
            <AnimatedCircularProgress
              value={stats.group_percentile ?? 0}
              size={100}
              strokeWidth={8}
              gradientFrom="#a855f7"
              gradientTo="#ec4899"
              label="Рейтинг"
            />
            <div className="mt-2 text-center">
              <span className="text-xs text-muted-foreground">
                {stats.group_rank ?? '—'} из {stats.group_total ?? '—'}
              </span>
            </div>
          </div>
        </div>

        {stats.labs_overdue > 0 && (
          <div className="flex items-center gap-2 p-3 mt-4 bg-gradient-to-r from-orange-100 to-red-100 dark:from-orange-900/20 dark:to-red-900/20 rounded-lg text-orange-700 dark:text-orange-400 border border-orange-200 dark:border-orange-800">
            <AlertTriangle className="w-5 h-5 shrink-0" />
            <span className="text-sm font-medium">
              {stats.labs_overdue} {stats.labs_overdue === 1 ? 'долг' : stats.labs_overdue < 5 ? 'долга' : 'долгов'} по лабораторным
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
