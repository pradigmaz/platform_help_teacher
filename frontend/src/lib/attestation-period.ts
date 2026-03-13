import { addWeeks, isBefore } from 'date-fns';

import type { SemesterInfo } from '@/hooks/useSemesterInfo';

export const ATTESTATION_WEEKS = {
  first: 8,
  second: 14,
} as const;

export function getAttestationPeriodDates(
  period: 'first' | 'second',
  semesterStart: Date
): { start: Date; end: Date } {
  if (period === 'first') {
    return {
      start: semesterStart,
      end: addWeeks(semesterStart, ATTESTATION_WEEKS.first),
    };
  }

  return {
    start: semesterStart,
    end: addWeeks(semesterStart, ATTESTATION_WEEKS.second),
  };
}

export function getCurrentAttestationType(info: SemesterInfo, now = new Date()): 'first' | 'second' {
  const semesterStart = info.semesterStartDate
    ? new Date(info.semesterStartDate)
    : info.semester === 1
      ? new Date(info.academicYear, 8, 1)
      : new Date(info.academicYear + 1, 0, 1);

  const secondStart = addWeeks(semesterStart, ATTESTATION_WEEKS.first);
  return isBefore(now, secondStart) ? 'first' : 'second';
}
