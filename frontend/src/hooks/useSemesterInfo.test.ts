import { describe, expect, it } from 'vitest';

import { getCurrentSemesterInfo } from './useSemesterInfo';

describe('getCurrentSemesterInfo', () => {
  it('uses the previous academic year for spring semester dates', () => {
    expect(getCurrentSemesterInfo(new Date('2026-04-15T12:00:00Z'))).toEqual({
      academicYear: 2025,
      semester: 2,
    });
  });

  it('uses the current year for autumn semester dates', () => {
    expect(getCurrentSemesterInfo(new Date('2026-09-10T12:00:00Z'))).toEqual({
      academicYear: 2026,
      semester: 1,
    });
  });
});
