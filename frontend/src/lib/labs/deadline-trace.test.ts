import { describe, expect, it } from 'vitest';

import { getDeadlineTraceTokens } from './deadline-trace';

describe('getDeadlineTraceTokens', () => {
  it('returns compact manual-check tokens for teacher queue', () => {
    expect(
      getDeadlineTraceTokens({
        current_max_grade: 4,
        lesson_index: 2,
        extension_bonus: 1,
        has_extension: true,
        is_excused_origin: false,
        effective_deadline_5_lessons: 2,
        effective_deadline_4_lessons: 3,
        effective_deadline_5_date: '2026-03-08',
        effective_deadline_4_date: '2026-03-15',
      }),
    ).toEqual(['макс. 4', 'индекс 2', '+1 пар', '5→2', '5 до 08.03', '4→3', '4 до 15.03']);
  });

  it('omits optional tokens when trace is empty', () => {
    expect(
      getDeadlineTraceTokens({
        current_max_grade: 5,
        extension_bonus: 0,
        has_extension: false,
        is_excused_origin: false,
      }),
    ).toEqual(['макс. 5']);
  });
});
