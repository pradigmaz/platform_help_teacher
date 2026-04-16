import { describe, expect, it } from 'vitest';

import {
  getResolvedAcceptanceLabel,
  getResolvedLabGrade,
  getResolvedLabStatus,
  isLabAccepted,
  type StudentLabLike,
} from './progress';

describe('labs progress helpers', () => {
  it('prefers journal acceptance over submission workflow status', () => {
    const lab = {
      is_accepted: true,
      acceptance_source: 'journal' as const,
      journal_grade: 4,
      submission: { id: 'sub-1', status: 'REJECTED' as const, grade: 2 },
    };

    expect(isLabAccepted(lab)).toBe(true);
    expect(getResolvedLabStatus(lab)).toBe('accepted');
    expect(getResolvedLabGrade(lab)).toBe(4);
    expect(getResolvedAcceptanceLabel(lab)).toBe('Зачтено');
  });

  it('falls back to submission workflow when journal acceptance is absent', () => {
    const lab = {
      is_accepted: false,
      acceptance_source: null,
      journal_grade: 2,
      submission: { id: 'sub-2', status: 'READY' as const, grade: undefined },
    };

    expect(isLabAccepted(lab)).toBe(false);
    expect(getResolvedLabStatus(lab)).toBe('rejected');
    expect(getResolvedLabGrade(lab)).toBe(2);
    expect(getResolvedAcceptanceLabel(lab)).toBe('Не сдано');
  });

  it('does not return null submission grades as a visible score', () => {
    const lab = {
      is_accepted: false,
      acceptance_source: null,
      journal_grade: null,
      submission: { id: 'sub-3', status: 'READY' as const, grade: null },
    } as unknown as StudentLabLike;

    expect(getResolvedLabGrade(lab)).toBeUndefined();
    expect(getResolvedLabStatus(lab)).toBe('pending');
  });
});
