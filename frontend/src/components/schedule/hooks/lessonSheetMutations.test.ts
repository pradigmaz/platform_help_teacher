import { describe, expect, it } from 'vitest';

import {
  hasResolvedGradeWorkNumber,
  stripIncompleteGradeSelections,
} from './lessonSheetMutations';

describe('lessonSheetMutations', () => {
  it('requires either a selected or default lab number before applying a grade', () => {
    expect(hasResolvedGradeWorkNumber(null, null)).toBe(false);
    expect(hasResolvedGradeWorkNumber(5, null)).toBe(true);
    expect(hasResolvedGradeWorkNumber(null, 5)).toBe(true);
  });

  it('drops incomplete single-grade selections without a lab number from draft state', () => {
    expect(
      stripIncompleteGradeSelections({
        missing: {
          grade: 5,
          work_number: null,
        },
        resolved: {
          grade: 4,
          work_number: 3,
        },
        conflict: {
          grade: null,
          work_number: null,
          has_conflict: true,
          conflict_count: 2,
          grade_items: [{ grade: 5, work_number: null }],
        },
        multi: {
          grade: 5,
          work_number: 1,
          grade_items: [
            { grade: 5, work_number: 1 },
            { grade: 4, work_number: 2 },
          ],
        },
      })
    ).toEqual({
      resolved: {
        grade: 4,
        work_number: 3,
      },
      conflict: {
        grade: null,
        work_number: null,
        has_conflict: true,
        conflict_count: 2,
        grade_items: [{ grade: 5, work_number: null }],
      },
      multi: {
        grade: 5,
        work_number: 1,
        grade_items: [
          { grade: 5, work_number: 1 },
          { grade: 4, work_number: 2 },
        ],
      },
    });
  });
});
