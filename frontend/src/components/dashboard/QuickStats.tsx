'use client';

import Link from 'next/link';
import { MagicCard } from '@/components/ui/magic-card';
import { Progress } from '@/components/ui/progress';
import { SlidingNumber } from '@/components/animate-ui/primitives/texts/sliding-number';
import { Effects } from '@/components/animate-ui/primitives/effects/effect';
import { IconFlask, IconCalendar, IconClock } from '@tabler/icons-react';
import type { QuickStatsProps } from './types';

/** Calculate lab statistics */
function getLabStats(labs: QuickStatsProps['labs'], attestation?: QuickStatsProps['attestation']) {
  // visible = labs available to student (attached to lessons)
  const visible = labs.length;
  const accepted = labs.filter(l => l.submission?.status === 'ACCEPTED').length;
  const pending = labs.filter(l => l.submission?.status === 'IN_REVIEW' || l.submission?.status === 'READY').length;
  // required = total labs needed for attestation
  const required = attestation?.breakdown?.labs?.required ?? visible;
  const percent = required > 0 ? Math.round((visible / required) * 100) : 0;
  return { visible, accepted, pending, required, percent };
}

/** Get nearest deadline (by lessons count) */
function getNearestDeadline(labs: QuickStatsProps['labs']): { title: string; lessonsLeft: number } | null {
  const upcoming = labs
    .filter(l => l.deadline_5_lessons && l.submission?.status !== 'ACCEPTED')
    .sort((a, b) => (a.deadline_5_lessons ?? Infinity) - (b.deadline_5_lessons ?? Infinity));
  
  if (upcoming.length === 0) return null;
  return { title: upcoming[0].title, lessonsLeft: upcoming[0].deadline_5_lessons! };
}

/** Format lessons left */
function formatLessonsLeft(lessons: number): string {
  if (lessons === 1) return 'След. пара';
  return `Через ${lessons - 1} пар`;
}

/**
 * Quick stats cards: Labs, Attendance, Deadline
 */
export function QuickStats({ labs, attendance, attestation, isLoading }: QuickStatsProps) {
  if (isLoading) {
    return <QuickStatsSkeleton />;
  }

  const labStats = getLabStats(labs, attestation);
  const attendanceRate = attendance?.stats.attendance_rate || 0;
  const nearestDeadline = getNearestDeadline(labs);

  return (
    <Effects fade slide={{ direction: 'up', offset: 30 }} holdDelay={100} inView inViewOnce>
      {/* Labs Card */}
      <Link href="/dashboard/labs">
        <MagicCard gradientColor="#8b5cf620" className="cursor-pointer hover:scale-[1.02] transition-transform">
          <div className="p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 rounded-lg bg-purple-500/10">
                <IconFlask className="h-5 w-5 text-purple-500" />
              </div>
              <span className="text-sm font-medium text-muted-foreground">Лабораторные</span>
            </div>
            
            <div className="flex items-baseline gap-1 mb-2">
              <span className="text-3xl font-bold text-purple-500">
                <SlidingNumber number={labStats.visible} />
              </span>
              <span className="text-lg text-muted-foreground">/{labStats.required}</span>
            </div>
            
            <Progress value={labStats.percent} className="h-1.5 [&>div]:bg-purple-500" />
            
            {labStats.accepted > 0 && (
              <p className="text-xs text-muted-foreground mt-2">
                Сдано: {labStats.accepted}
              </p>
            )}
          </div>
        </MagicCard>
      </Link>

      {/* Attendance Card */}
      <Link href="/dashboard/attendance">
        <MagicCard gradientColor="#3b82f620" className="cursor-pointer hover:scale-[1.02] transition-transform">
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
      </Link>

      {/* Deadline Card */}
      <MagicCard gradientColor="#f9731620" className="cursor-pointer hover:scale-[1.02] transition-transform">
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
                {formatLessonsLeft(nearestDeadline.lessonsLeft)}
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
