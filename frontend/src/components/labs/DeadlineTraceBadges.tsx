'use client';

import { Badge } from '@/components/ui/badge';
import { getDeadlineTraceTokens } from '@/lib/labs/deadline-trace';
import type { StudentDeadlineTrace } from '@/lib/api/types/student';
import type { SubmissionDeadlineTrace } from '@/lib/api/types/lab-queue';

type DeadlineTraceBadgesProps = {
  trace?: StudentDeadlineTrace | SubmissionDeadlineTrace | null;
  className?: string;
};

export function DeadlineTraceBadges({ trace, className }: DeadlineTraceBadgesProps) {
  const tokens = getDeadlineTraceTokens(trace);
  if (tokens.length === 0) {
    return null;
  }

  return (
    <div className={className ?? 'flex flex-wrap gap-2'}>
      {tokens.map((token) => (
        <Badge key={token} variant="outline" className="text-xs">
          {token}
        </Badge>
      ))}
    </div>
  );
}
