'use client';

import { FlaskConical, Calendar } from 'lucide-react';
import { BlurFade } from '@/components/ui/blur-fade';
import { MagicCard } from '@/components/ui/magic-card';
import { NumberTicker } from '@/components/ui/number-ticker';
import { AnimatedCircularProgress } from '@/components/ui/animated-circular-progress';

interface StatsCardsProps {
  completedLabs: number;
  plannedLabs: number;
  progressPercent: number;
}

export function StatsCards({ completedLabs, plannedLabs, progressPercent }: StatsCardsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <BlurFade delay={0.15}>
        <MagicCard className="cursor-pointer group" gradientColor="#8b5cf620">
          <div className="p-6 text-center relative overflow-hidden">
            <div className="absolute top-2 right-2 opacity-10 group-hover:opacity-20 transition-opacity">
              <FlaskConical className="w-12 h-12 text-purple-500" />
            </div>
            <div className="text-4xl font-bold text-purple-600 dark:text-purple-400">
              <NumberTicker value={completedLabs} />
            </div>
            <div className="text-sm text-muted-foreground mt-1 font-medium">Создано лаб</div>
          </div>
        </MagicCard>
      </BlurFade>

      <BlurFade delay={0.2}>
        <MagicCard className="cursor-pointer group" gradientColor="#3b82f620">
          <div className="p-6 text-center relative overflow-hidden">
            <div className="absolute top-2 right-2 opacity-10 group-hover:opacity-20 transition-opacity">
              <Calendar className="w-12 h-12 text-blue-500" />
            </div>
            <div className="text-4xl font-bold text-blue-600 dark:text-blue-400">
              <NumberTicker value={plannedLabs} />
            </div>
            <div className="text-sm text-muted-foreground mt-1 font-medium">Запланировано</div>
          </div>
        </MagicCard>
      </BlurFade>

      <BlurFade delay={0.25}>
        <MagicCard className="cursor-pointer group" gradientColor="#22c55e20">
          <div className="p-6 flex items-center justify-center gap-4">
            <AnimatedCircularProgress
              value={progressPercent}
              size={80}
              strokeWidth={6}
              gradientFrom="#22c55e"
              gradientTo="#10b981"
              label=""
            />
            <div>
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">{progressPercent}%</div>
              <div className="text-sm text-muted-foreground">Прогресс</div>
            </div>
          </div>
        </MagicCard>
      </BlurFade>
    </div>
  );
}
