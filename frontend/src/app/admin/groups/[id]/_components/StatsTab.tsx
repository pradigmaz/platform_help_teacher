'use client';

import { BarChart3 } from 'lucide-react';

export function StatsTab() {
  return (
    <div className="text-center py-12 border rounded-xl">
      <BarChart3 className="w-12 h-12 mx-auto text-muted-foreground/30 mb-4" />
      <p className="text-muted-foreground">Статистика будет доступна позже</p>
      <p className="text-sm text-muted-foreground mt-1">Посещаемость, оценки, активность</p>
    </div>
  );
}
