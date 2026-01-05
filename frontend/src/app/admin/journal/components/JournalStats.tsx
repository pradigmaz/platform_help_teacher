'use client';

import { TrendingUp, BarChart3 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import type { JournalStats as JournalStatsType } from '../lib/journal-constants';

interface JournalStatsProps {
  stats: JournalStatsType;
}

export function JournalStats({ stats }: JournalStatsProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
      <Card>
        <CardContent className="pt-4">
          <div className="text-2xl font-bold">{stats.total_lessons}</div>
          <p className="text-xs text-muted-foreground">Занятий</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-4">
          <div className="text-2xl font-bold text-blue-600">{stats.lectures}</div>
          <p className="text-xs text-muted-foreground">Лекций</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-4">
          <div className="text-2xl font-bold text-purple-600">{stats.labs}</div>
          <p className="text-xs text-muted-foreground">Лабораторных</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-4">
          <div className="text-2xl font-bold text-green-600">{stats.practices}</div>
          <p className="text-xs text-muted-foreground">Практик</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-muted-foreground" />
            <span className="text-2xl font-bold">
              {stats.attendance_rate !== null ? `${stats.attendance_rate}%` : '—'}
            </span>
          </div>
          {stats.attendance_rate !== null && (
            <Progress value={stats.attendance_rate} className="mt-2 h-1" />
          )}
          <p className="text-xs text-muted-foreground mt-1">Посещаемость</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-muted-foreground" />
            <span className="text-2xl font-bold">
              {stats.average_grade !== null ? stats.average_grade : '—'}
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">Средний балл</p>
        </CardContent>
      </Card>
    </div>
  );
}
