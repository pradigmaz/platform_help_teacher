'use client';

import { BookOpenCheck, FlaskConical, UploadCloud } from 'lucide-react';
import { BlurFade } from '@/components/ui/blur-fade';
import { MetricCard } from '@/components/ui/metric-card';
import { NumberTicker } from '@/components/ui/number-ticker';

interface StatsCardsProps {
  createdLabs: number;
  publishedLabs: number;
  selectedSubjectName: string;
}

export function StatsCards({ createdLabs, publishedLabs, selectedSubjectName }: StatsCardsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <BlurFade delay={0.15}>
        <MetricCard tint="purple" className="cursor-pointer group">
          <div className="p-6 text-center relative overflow-hidden">
            <div className="absolute top-2 right-2 opacity-10 group-hover:opacity-20 transition-opacity">
              <FlaskConical className="w-12 h-12 text-purple-500" />
            </div>
            <div className="text-4xl font-bold text-purple-600 dark:text-purple-400">
              <NumberTicker value={createdLabs} />
            </div>
            <div className="text-sm text-muted-foreground mt-1 font-medium">Создано лаб</div>
          </div>
        </MetricCard>
      </BlurFade>

      <BlurFade delay={0.2}>
        <MetricCard tint="blue" className="cursor-pointer group">
          <div className="p-6 text-center relative overflow-hidden">
            <div className="absolute top-2 right-2 opacity-10 group-hover:opacity-20 transition-opacity">
              <UploadCloud className="w-12 h-12 text-blue-500" />
            </div>
            <div className="text-4xl font-bold text-blue-600 dark:text-blue-400">
              <NumberTicker value={publishedLabs} />
            </div>
            <div className="text-sm text-muted-foreground mt-1 font-medium">Опубликовано</div>
          </div>
        </MetricCard>
      </BlurFade>

      <BlurFade delay={0.25}>
        <MetricCard tint="green" className="cursor-pointer group">
          <div className="relative flex min-h-[96px] flex-col justify-center overflow-hidden p-5">
            <div className="absolute top-2 right-2 opacity-10 group-hover:opacity-20 transition-opacity">
              <BookOpenCheck className="w-12 h-12 text-green-500" />
            </div>
            <div className="text-xs font-medium uppercase tracking-normal text-muted-foreground">
              Текущий предмет
            </div>
            <div className="mt-2 max-w-[90%] whitespace-normal break-words text-lg font-semibold leading-snug text-green-600 dark:text-green-400">
              {selectedSubjectName || 'Предмет не выбран'}
            </div>
          </div>
        </MetricCard>
      </BlurFade>
    </div>
  );
}
