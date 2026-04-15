import { describe, expect, it } from 'vitest';
import {
  filterStudentsBySubgroup,
  getAttendanceDistributionForSubgroup,
  getAvailableSubgroups,
  getLabProgressForSubgroup,
} from './reportFilters';

describe('reportFilters', () => {
  const baseData = {
    has_subgroups: true,
    students: [
      { id: '1', subgroup: 1, needs_attention: false },
      { id: '2', subgroup: 2, needs_attention: false },
      { id: '3', needs_attention: false },
    ],
    attendance_stats: {
      distribution: { present: 8, late: 1, excused: 0, absent: 1 },
      by_subgroup: {
        '1': { present: 4, late: 0, excused: 0, absent: 1 },
        '2': { present: 4, late: 1, excused: 0, absent: 0 },
      },
      trend: [],
      average_rate: 82,
    },
    lab_progress_by_subgroup: {
      '1': [{ lab_name: 'Л1', completed_count: 3, total_students: 4, completion_rate: 75 }],
    },
  };

  it('returns available subgroup filters from report data', () => {
    expect(getAvailableSubgroups(baseData as never)).toEqual(['all', '1', '2']);
  });

  it('filters students by subgroup without mutating the full list', () => {
    const result = filterStudentsBySubgroup(baseData.students as never, '1');

    expect(result).toHaveLength(1);
    expect(result[0].id).toBe('1');
    expect(baseData.students).toHaveLength(3);
  });

  it('selects subgroup-specific attendance distribution when available', () => {
    expect(
      getAttendanceDistributionForSubgroup(undefined, baseData.attendance_stats as never, '2'),
    ).toEqual({ present: 4, late: 1, excused: 0, absent: 0 });
  });

  it('selects subgroup-specific lab progress when available', () => {
    expect(
      getLabProgressForSubgroup(undefined, baseData.lab_progress_by_subgroup, '1'),
    ).toEqual([{ lab_name: 'Л1', completed_count: 3, total_students: 4, completion_rate: 75 }]);
  });
});
