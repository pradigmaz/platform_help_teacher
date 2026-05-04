'use client';

import { CardSpotlight } from '@/components/ui/card-spotlight';

interface LabsProgressCardProps {
  acceptedCount: number;
  totalCount: number;
  progress: number;
}

export function LabsProgressCard({ acceptedCount, totalCount, progress }: LabsProgressCardProps) {
  return (
    <CardSpotlight className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-foreground">Прогресс по выбранному предмету</h3>
          <p className="text-sm text-muted-foreground">Сдано {acceptedCount} из {totalCount} работ</p>
        </div>
        <div className="text-3xl font-bold text-green-500">{progress}%</div>
      </div>
      <div className="relative h-3 bg-muted/50 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-green-500 to-emerald-400 transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>
    </CardSpotlight>
  );
}

