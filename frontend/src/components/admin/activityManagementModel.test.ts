import { describe, expect, it } from 'vitest';

import { getActivityInitials, groupActivitiesByBatch } from './activityManagementModel';

describe('activityManagementModel', () => {
  it('groups batch activities together', () => {
    const grouped = groupActivitiesByBatch([
      { id: '1', batch_id: 'batch-1', group_name: 'ИС-24-1' } as never,
      { id: '2', batch_id: 'batch-1', group_name: 'ИС-24-1' } as never,
      { id: '3', batch_id: null, group_name: 'ИС-24-2' } as never,
    ]);

    expect(grouped.map((entry) => entry.key)).toEqual(['batch-1', '3']);
    expect(grouped[0].isGroup).toBe(true);
    expect(grouped[1].isGroup).toBe(false);
  });

  it('builds initials from student names', () => {
    expect(getActivityInitials('Иванов Иван Иванович')).toBe('ИИ');
  });
});
