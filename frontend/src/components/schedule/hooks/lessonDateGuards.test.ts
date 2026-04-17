import { describe, expect, it } from 'vitest';

import { getMskDate, isFutureLessonDate } from './lessonDateGuards';

describe('lessonDateGuards', () => {
  it('uses Moscow date for today checks', () => {
    expect(getMskDate(new Date('2026-04-17T21:30:00.000Z'))).toBe('2026-04-18');
  });

  it('detects future lesson dates by ISO date', () => {
    expect(isFutureLessonDate('2026-04-18', '2026-04-17')).toBe(true);
    expect(isFutureLessonDate('2026-04-17', '2026-04-17')).toBe(false);
    expect(isFutureLessonDate('2026-04-16', '2026-04-17')).toBe(false);
  });
});
