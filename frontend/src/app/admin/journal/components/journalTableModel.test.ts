import { describe, expect, it } from 'vitest';

import {
  buildMaxWorkNumberMap,
  calculateAttendancePercentage,
  isJournalStudentLessonStateEqual,
  isLessonDisabledForStudent,
  sortJournalLessons,
} from './journalTableModel';

const lessons = [
  {
    id: 'b',
    date: '2026-03-11',
    lesson_number: 2,
    lesson_type: 'PRACTICE',
    topic: 'B',
    work_number: 2,
    lecture_work_type: null,
    subgroup: null,
    is_cancelled: false,
    subject_id: 's',
    subject_name: 'Math',
  },
  {
    id: 'a',
    date: '2026-03-11',
    lesson_number: 1,
    lesson_type: 'PRACTICE',
    topic: 'A',
    work_number: 1,
    lecture_work_type: null,
    subgroup: 1,
    is_cancelled: false,
    subject_id: 's',
    subject_name: 'Math',
  },
] as const;

describe('journalTableModel', () => {
  it('sorts lessons by date and lesson number', () => {
    expect(sortJournalLessons([...lessons]).map((lesson) => lesson.id)).toEqual(['a', 'b']);
  });

  it('builds max work number map by lesson type', () => {
    expect(buildMaxWorkNumberMap([...lessons])).toEqual({ practice: 2 });
  });

  it('calculates attendance percentage from present and late statuses', () => {
    expect(
      calculateAttendancePercentage(
        [...lessons],
        {
          a: { student: 'PRESENT' },
          b: { student: 'LATE' },
        },
        'student'
      )
    ).toBe(100);
  });

  it('detects subgroup-disabled lessons', () => {
    expect(
      isLessonDisabledForStudent(lessons[0], {
        id: 'student',
        full_name: 'Иванов Иван',
        subgroup: 2,
      })
    ).toBe(false);
    expect(
      isLessonDisabledForStudent(lessons[1], {
        id: 'student',
        full_name: 'Иванов Иван',
        subgroup: 2,
      })
    ).toBe(true);
  });

  it('treats another student update as unchanged for the current row', () => {
    expect(
      isJournalStudentLessonStateEqual(
        [...lessons],
        'student-a',
        {
          a: { 'student-a': 'PRESENT', 'student-b': 'ABSENT' },
          b: { 'student-a': 'LATE' },
        },
        {
          a: { 'student-a': 'PRESENT', 'student-b': 'PRESENT' },
          b: { 'student-a': 'LATE' },
        },
        {
          a: {
            'student-a': { grade: 5, work_number: 1 },
            'student-b': { grade: 2, work_number: 1 },
          },
        },
        {
          a: {
            'student-a': { grade: 5, work_number: 1 },
            'student-b': { grade: 4, work_number: 1 },
          },
        },
      ),
    ).toBe(true);
  });

  it('detects changes in the current student lesson state', () => {
    expect(
      isJournalStudentLessonStateEqual(
        [...lessons],
        'student-a',
        {
          a: { 'student-a': 'PRESENT' },
          b: { 'student-a': 'LATE' },
        },
        {
          a: { 'student-a': 'ABSENT' },
          b: { 'student-a': 'LATE' },
        },
        {
          a: { 'student-a': { grade: 5, work_number: 1 } },
        },
        {
          a: { 'student-a': { grade: 4, work_number: 1 } },
        },
      ),
    ).toBe(false);
  });
});
