'use client';

import { Card } from '@/components/ui/card';

interface ChartTooltipCardProps {
  title: string;
  value: string;
  description?: string;
}

export function ChartTooltipCard({ title, value, description }: ChartTooltipCardProps) {
  return (
    <Card className="max-w-[220px] rounded-2xl border-border/60 bg-card/95 px-3 py-2 shadow-lg">
      <div className="space-y-1">
        <p className="break-words text-xs font-medium leading-snug text-foreground">
          {title}
        </p>
        <p className="text-sm font-semibold text-foreground">{value}</p>
        {description && (
          <p className="break-words text-[11px] leading-snug text-muted-foreground">
            {description}
          </p>
        )}
      </div>
    </Card>
  );
}
