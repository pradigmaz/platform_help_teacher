'use client';

import { cn } from '@/lib/utils';
import { MagicCard } from '@/components/ui/magic-card';
import { Progress } from '@/components/ui/progress';
import { SlidingNumber } from '@/components/animate-ui/primitives/texts/sliding-number';
import { Effects } from '@/components/animate-ui/primitives/effects/effect';
import { IconFlask, IconCalendar, IconClock } from '@tabler/icons-react';
import type { QuickStatsProps } from './types';

/** Calculate lab statistics */
function getLabStats(labs: QuickStatsProps['labs']) {
  const total = labs.length;
  const accepted = labs.filter(l => l.submission?.status === 'ACCEPTED').length;
  const pending = labs.filter(l => l.submission?.status === 'IN_REVIEW' || l.submission?.status === 'READY').length;
  const percent = total > 0 ? Math.round((accepted / total) * 100) : 0;
  return { total, accepted, pending, percent };
}

/** Get nearest deadline */
function getNearestDeadline(labs: QuickStatsProps['labs']): { title: string; date: Date } | null {
  const now = new Date();
  const upcoming = labs
    .filter(l => l.deadline && new Date(l.deadline) > now && l.submission?.status !== 'ACCEPTED')
    .sort((a, b) => new Date(a.deadline!).getTime() - new Date(b.deadline!).getTime());
  
  if (upcoming.length === 0) return null;
  return { title: upcoming[0].title, date: new Date(upcoming[0].deadline!) };
}

/** Format date to short string */
function formatShortDate(date: Date): string {
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
}

/**
 * Quick stats cards: Labs, Attendance, Deadline
 */
export function QuickStats({ labs, attendance, isLoading }: QuickStatsProps) {
  if (isLoading) {
    return <QuickStatsSkeleton />;
  }

  const labStats = getLabStats(labs);
  const attendanceRate = attendance?.stats.attendance_rate || 0;
  const nearestDeadline = getNearestDeadline(labs);

  return (
    <Effects fade slide={{ direction: 'up', offset: 30 }} holdDelay={100} inView inViewOnce>
      {/* Labs Card */}
      <MagicCard gradientColor="#8b5cf620" className="cursor-pointer">
        <div className="p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-purple-500/10">
              <IconFlask className="h-5 w-5 text-purple-500" />
            </div>
            <span className="text-sm font-medium text-muted-foreground">Лабораторные</span>
          </div>
          
          <div className="flex items-baseline gap-1 mb-2">
            <span className="text-3xl font-bold text-purple-500">
              <SlidingNumber number={labStats.accepted} />
            </span>
            <span className="text-lg text-muted-foreground">/{labStats.total}</span>
          </div>
          
          <Progress value={labStats.percent} className="h-1.5 [&>div]:bg-purple-500" />
          
          {labStats.pending > 0 && (
            <p className="text-xs text-muted-foreground mt-2">
              На проверке: {labStats.pending}
            </p>
          )}
        </div>
      </MagicCard>

      {/* Attendance Card */}
      <MagicCard gradientColor="#3b82f620" className="cursor-pointer">
        <div className="p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-blue-500/10">
              <IconCalendar className="h-5 w-5 text-blue-500" />
            </div>
            <span className="text-sm font-medium text-muted-foreground">Посещаемость</span>
          </div>
          
          {attendance && attendance.stats.total_classes > 0 ? (
            <>
              <div className="flex items-baseline gap-1 mb-2">
                <span className="text-3xl font-bold text-blue-500">
                  <SlidingNumber number={Math.round(attendanceRate)} />
                </span>
                <span className="text-lg text-muted-foreground">%</span>
              </div>
              
              <div className="flex gap-3 text-xs text-muted-foreground">
                <span className="text-green-500">✓ {attendance.stats.present}</span>
                <span className="text-yellow-500">⏰ {attendance.stats.late}</span>
                <span className="text-red-500">✗ {attendance.stats.absent}</span>
              </div>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">Нет данных</p>
          )}
        </div>
      </MagicCard>

      {/* Deadline Card */}
      <MagicCard gradientColor="#f9731620" className="cursor-pointer">
        <div className="p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-orange-500/10">
              <IconClock className="h-5 w-5 text-orange-500" />
            </div>
            <span className="text-sm font-medium text-muted-foreground">Ближайший дедлайн</span>
          </div>
          
          {nearestDeadline ? (
            <>
              <p className="text-lg font-semibold text-foreground truncate mb-1">
                {nearestDeadline.title}
              </p>
              <p className="text-2xl font-bold text-orange-500">
                {formatShortDate(nearestDeadline.date)}
              </p>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">Нет активных дедлайнов</p>
          )}
        </div>
      </MagicCard>
    </Effects>
  );
}

function QuickStatsSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {[1, 2, 3].map(i => (
        <MagicCard key={i} gradientColor="#71717a20">
          <div className="p-5 animate-pulse">
            <div className="h-5 w-20 bg-muted rounded mb-3" />
            <div className="h-8 w-16 bg-muted rounded mb-2" />
            <div className="h-1.5 bg-muted rounded" />
          </div>
        </MagicCard>
      ))}
    </div>
  );
}
