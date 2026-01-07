'use client';

import { cn } from '@/lib/utils';
import type { EmptyStateProps } from './types';

/**
 * Empty state component for when data is unavailable
 */
export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className={cn(
      "flex flex-col items-center justify-center py-8 px-4 text-center",
      "rounded-lg border border-dashed border-border bg-muted/30"
    )}>
      {icon && (
        <div className="mb-3 text-muted-foreground/60">
          {icon}
        </div>
      )}
      <h4 className="text-sm font-medium text-foreground mb-1">
        {title}
      </h4>
      {description && (
        <p className="text-xs text-muted-foreground max-w-[200px]">
          {description}
        </p>
      )}
      {action && (
        <div className="mt-4">
          {action}
        </div>
      )}
    </div>
  );
}
