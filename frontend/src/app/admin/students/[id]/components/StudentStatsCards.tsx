'use client';

import { CheckCircle, Clock, Flame, Target } from 'lucide-react';
import { NumberTicker } from '@/components/ui/number-ticker';
import { BlurFade } from '@/components/ui/blur-fade';
import { MagicCard } from '@/components/ui/magic-card';
import { StudentStats } from './types';

interface Props {
  stats: StudentStats;
}

export function StudentStatsCards({ stats }: Props) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <BlurFade delay={0.3}>
        <MagicCard className="cursor-pointer group" gradientColor="#22c55e20">
          <div className="p-6 text-center relative overflow-hidden">
            <div className="absolute top-2 right-2 opacity-10 group-hover:opacity-20 transition-opacity">
              <CheckCircle className="w-12 h-12 text-green-500 dark:text-green-400" />
            </div>
            <div className="text-4xl font-bold text-green-600 dark:text-green-400">
              <NumberTicker value={stats.labs_accepted} />
            </div>
            <div className="text-sm text-muted-foreground mt-1 font-medium">Сдано</div>
          </div>
        </MagicCard>
      </BlurFade>
      
      <BlurFade delay={0.35}>
        <MagicCard className="cursor-pointer group" gradientColor="#eab30820">
          <div className="p-6 text-center relative overflow-hidden">
            <div className="absolute top-2 right-2 opacity-10 group-hover:opacity-20 transition-opacity">
              <Clock className="w-12 h-12 text-yellow-500 dark:text-yellow-400" />
            </div>
            <div className="text-4xl font-bold text-yellow-600 dark:text-yellow-400">
              <NumberTicker value={stats.labs_pending} />
            </div>
            <div className="text-sm text-muted-foreground mt-1 font-medium">На проверке</div>
          </div>
        </MagicCard>
      </BlurFade>
      
      <BlurFade delay={0.4}>
        <MagicCard className="cursor-pointer group" gradientColor="#f9731620">
          <div className="p-6 text-center relative overflow-hidden">
            <div className="absolute top-2 right-2 opacity-10 group-hover:opacity-20 transition-opacity">
              <Flame className="w-12 h-12 text-orange-500 dark:text-orange-400" />
            </div>
            <div className="text-4xl font-bold text-orange-600 dark:text-orange-400">
              <NumberTicker value={stats.labs_overdue} />
            </div>
            <div className="text-sm text-muted-foreground mt-1 font-medium">Долги</div>
          </div>
        </MagicCard>
      </BlurFade>
      
      <BlurFade delay={0.45}>
        <MagicCard className="cursor-pointer group" gradientColor="#3b82f620">
          <div className="p-6 text-center relative overflow-hidden">
            <div className="absolute top-2 right-2 opacity-10 group-hover:opacity-20 transition-opacity">
              <Target className="w-12 h-12 text-blue-500 dark:text-blue-400" />
            </div>
            <div className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-cyan-500 dark:from-blue-400 dark:to-cyan-400 bg-clip-text text-transparent">
              <NumberTicker value={stats.points_percent} decimalPlaces={0} />%
            </div>
            <div className="text-sm text-muted-foreground mt-1 font-medium">Успеваемость</div>
          </div>
        </MagicCard>
      </BlurFade>
    </div>
  );
}
