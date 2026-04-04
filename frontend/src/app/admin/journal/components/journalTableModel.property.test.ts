import { describe, expect, it } from 'vitest';
import fc from 'fast-check';
import {
  calculateAttendancePercentage,
  sortJournalLessons,
} from './journalTableModel';
import type { Lesson } from '../lib/journal-constants';

const lessonArb: fc.Arbitrary<Lesson> = fc.record({
  id: fc.uuid(),
  date: fc
    .record({
      year: fc.integer({ min: 2020, max: 2035 }),
      month: fc.integer({ min: 1, max: 12 }),
      day: fc.integer({ min: 1, max: 28 }),
    })
    .map(({ year, month, day }) => `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`),
  lesson_number: fc.integer({ min: 1, max: 8 }),
  lesson_type: fc.constantFrom('LECTURE', 'PRACTICE', 'LAB'),
  topic: fc.option(fc.string({ minLength: 1, maxLength: 12 }), { nil: null }),
  work_number: fc.option(fc.integer({ min: 1, max: 10 }), { nil: null }),
  lecture_work_type: fc.option(fc.string({ minLength: 1, maxLength: 8 }), { nil: null }),
  subgroup: fc.option(fc.integer({ min: 1, max: 3 }), { nil: null }),
  is_cancelled: fc.boolean(),
  subject_id: fc.option(fc.uuid(), { nil: null }),
  subject_name: fc.option(fc.string({ minLength: 1, maxLength: 12 }), { nil: null }),
});

describe('journalTableModel property tests', () => {
  it('sortJournalLessons keeps lessons ordered by date then lesson number', () => {
    fc.assert(
      fc.property(fc.uniqueArray(lessonArb, { selector: (lesson) => lesson.id, minLength: 1, maxLength: 20 }), (lessons) => {
        const sorted = sortJournalLessons(lessons);
        expect(sorted.map((lesson) => lesson.id).sort()).toEqual(lessons.map((lesson) => lesson.id).sort());

        for (let index = 1; index < sorted.length; index += 1) {
          const previous = sorted[index - 1];
          const current = sorted[index];
          expect(
            previous.date < current.date ||
              (previous.date === current.date && previous.lesson_number <= current.lesson_number)
          ).toBe(true);
        }
      })
    );
  });

  it('calculateAttendancePercentage stays within null-or-0..100 range', () => {
    fc.assert(
      fc.property(
        fc.uniqueArray(lessonArb, { selector: (lesson) => lesson.id, minLength: 1, maxLength: 20 }),
        fc.dictionary(fc.uuid(), fc.constantFrom('PRESENT', 'LATE', 'ABSENT', 'EXCUSED')),
        (lessons, statuses) => {
          const attendance: Record<string, Record<string, string>> = {};
          const studentStatus = statuses.student;
          for (const lesson of lessons) {
            attendance[lesson.id] = studentStatus ? { student: studentStatus } : {};
          }
          const percentage = calculateAttendancePercentage(lessons, attendance, 'student');
          if (percentage === null) {
            expect(percentage).toBeNull();
          } else {
            expect(percentage).toBeGreaterThanOrEqual(0);
            expect(percentage).toBeLessThanOrEqual(100);
          }
        }
      )
    );
  });
});
