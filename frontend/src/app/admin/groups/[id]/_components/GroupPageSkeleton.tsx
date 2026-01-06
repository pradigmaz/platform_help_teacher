'use client';

import { Skeleton } from '@/components/ui/skeleton';

export function GroupPageSkeleton() {
  return (
    <div className="max-w-6xl mx-auto p-8">
      {/* Header Skeleton */}
      <div className="flex items-center gap-4 mb-6">
        <Skeleton className="w-10 h-10 rounded-md" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
      </div>

      {/* Tabs Skeleton */}
      <div className="flex gap-4 border-b mb-6 pb-2">
        <Skeleton className="h-8 w-24" />
        <Skeleton className="h-8 w-24" />
        <Skeleton className="h-8 w-24" />
      </div>

      {/* Table Skeleton */}
      <div className="border rounded-xl overflow-hidden">
        <div className="bg-muted/50 h-12 w-full" />
        <div className="divide-y">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="px-4 py-4 flex items-center justify-between">
              <div className="flex items-center gap-4 flex-1">
                <Skeleton className="h-4 w-8" />
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-4 w-32" />
              </div>
              <Skeleton className="h-8 w-8 rounded-md" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
