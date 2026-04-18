import { describe, expect, it } from 'vitest';

import { buildGradeUpdates } from './lessonSheetState';

describe('buildGradeUpdates', () => {
  it('skips unchanged single-grade cells from schedule save payload', () => {
    const singleGrade = {
      grade: 5,
      work_number: 5,
      has_conflict: false,
      conflict_count: 0,
      grade_items: [{ grade: 5, work_number: 5 }],
    };

    expect(buildGradeUpdates({ student: singleGrade }, { student: singleGrade })).toEqual([]);
  });

  it('skips unchanged multi-grade cells from schedule save payload', () => {
    const multiGrade = {
      grade: 5,
      work_number: 5,
      has_conflict: false,
      conflict_count: 0,
      grade_items: [
        { grade: 5, work_number: 5 },
        { grade: 5, work_number: 10 },
      ],
    };

    expect(buildGradeUpdates({ student: multiGrade }, { student: multiGrade })).toEqual([]);
  });

  it('still emits updates for regular single-grade cells', () => {
    expect(
      buildGradeUpdates(
        { student: { grade: 4, work_number: 5 } },
        { student: { grade: 5, work_number: 5 } }
      )
    ).toEqual([{ student_id: 'student', grade: 5, work_number: 5 }]);
  });
});
