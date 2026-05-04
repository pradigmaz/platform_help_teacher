import { describe, expect, it } from 'vitest';

import type { LessonResponse } from '@/lib/api/types/schedule';
import { mapScheduleLesson } from './scheduleViewModel';

describe('scheduleViewModel', () => {
  it('preserves subject scope for regular lesson sheets', () => {
    const lesson: LessonResponse = {
      id: 'lesson-1',
      group_id: 'group-1',
      date: '2026-04-20',
      lesson_number: 2,
      lesson_type: 'lab',
      room: null,
      work_number: null,
      is_cancelled: false,
      ended_early: false,
      subject_id: 'subject-1',
      offering_id: 'offering-1',
      subject_name: 'Тестирование',
      group_name: 'ИС1',
      summary: null,
    };

    expect(mapScheduleLesson(lesson)).toMatchObject({
      subject_id: 'subject-1',
      offering_id: 'offering-1',
    });
  });
});
