'use client';

import { Skeleton } from '@/components/ui/skeleton';

export function LabsSkeleton() {
  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div className="space-y-2">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-48" />
      </div>
      <Skeleton className="h-24 rounded-xl" />
      <div className="flex gap-2">{[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-9 w-24 rounded-md" />)}</div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => <Skeleton key={i} className="h-48 rounded-xl" />)}
      </div>
    </div>
  );
}

