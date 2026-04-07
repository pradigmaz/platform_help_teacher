import { describe, expect, it } from 'vitest';

import { getMskNowSnapshot, isScheduleSlotPast } from './ScheduleGrid';

describe('ScheduleGrid temporal helpers', () => {
  it('builds Moscow date/time snapshot', () => {
    expect(getMskNowSnapshot(new Date('2026-04-07T12:15:00.000Z'))).toEqual({
      date: '2026-04-07',
      time: '15:15',
    });
  });

  it('treats previous days as past and future days as not past', () => {
    const now = { date: '2026-04-07', time: '15:15' };

    expect(isScheduleSlotPast('2026-04-06', 4, now)).toBe(true);
    expect(isScheduleSlotPast('2026-04-08', 1, now)).toBe(false);
  });

  it('uses lesson end time for current-day slot visibility', () => {
    expect(isScheduleSlotPast('2026-04-07', 4, { date: '2026-04-07', time: '15:05' })).toBe(false);
    expect(isScheduleSlotPast('2026-04-07', 4, { date: '2026-04-07', time: '15:11' })).toBe(true);
  });
});
