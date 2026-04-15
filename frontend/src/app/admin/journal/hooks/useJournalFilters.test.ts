import { renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  useSemesterInfo: vi.fn(),
}));

vi.mock('@/hooks/useSemesterInfo', () => ({
  useSemesterInfo: mocks.useSemesterInfo,
  getSemesterDates: vi.fn((academicYear: number, semester: 1 | 2, semesterStartDate: string) => ({
    start: new Date(`${semesterStartDate}T00:00:00`),
    end: new Date(
      semester === 1
        ? `${academicYear}-12-31T00:00:00`
        : `${academicYear + 1}-06-30T00:00:00`,
    ),
  })),
}));

import { sameSemesterInfo, useJournalFilters } from './useJournalFilters';

describe('useJournalFilters', () => {
  beforeEach(() => {
    mocks.useSemesterInfo.mockReturnValue({
      academicYear: 2025,
      semester: 2,
      semesterStartDate: '2026-01-12',
      loading: false,
    });
  });

  it('keeps week boundaries stable between rerenders when current week does not change', () => {
    const { result, rerender } = renderHook(() => useJournalFilters());
    const firstWeekStart = result.current.weekStart;
    const firstWeekEnd = result.current.weekEnd;

    rerender();

    expect(result.current.weekStart).toBe(firstWeekStart);
    expect(result.current.weekEnd).toBe(firstWeekEnd);
  });
});

describe('sameSemesterInfo', () => {
  it('returns true for identical semester selections', () => {
    expect(sameSemesterInfo(
      { academicYear: 2025, semester: 2 },
      { academicYear: 2025, semester: 2 },
    )).toBe(true);
  });

  it('returns false when academic year changes', () => {
    expect(sameSemesterInfo(
      { academicYear: 2025, semester: 2 },
      { academicYear: 2026, semester: 2 },
    )).toBe(false);
  });

  it('returns false when semester changes', () => {
    expect(sameSemesterInfo(
      { academicYear: 2025, semester: 1 },
      { academicYear: 2025, semester: 2 },
    )).toBe(false);
  });
});
