import { describe, expect, it, vi } from 'vitest';

import api from '@/lib/api';
import { loadLessonSheetResources } from './lessonSheetQueries';
import type { LessonSnapshot } from './lessonSheetState';

vi.mock('@/lib/api', () => ({
  default: {
    get: vi.fn(),
  },
}));

const apiGet = vi.mocked(api.get);

const lesson: LessonSnapshot = {
  id: 'lesson-1',
  group_id: 'group-1',
  subgroup: 2,
  subject_id: 'subject-1',
  topic: 'Тестирование информационных систем',
  work_number: null,
  is_cancelled: false,
  ended_early: false,
};

describe('loadLessonSheetResources', () => {
  it('loads lesson students from admin endpoint and keeps subgroup filtering', async () => {
    apiGet.mockImplementation(async (url: string) => {
      if (url === '/admin/groups/group-1/students') {
        return {
          data: [
            { id: 'student-1', full_name: 'Первый Студент', subgroup: 1 },
            { id: 'student-2', full_name: 'Второй Студент', subgroup: 2 },
          ],
        };
      }

      if (url === '/admin/journal/attendance') {
        return { data: [] };
      }

      if (url === '/admin/journal/grades') {
        return { data: [] };
      }

      if (url === '/admin/labs') {
        return { data: [] };
      }

      throw new Error(`Unexpected URL: ${url}`);
    });

    const resources = await loadLessonSheetResources(lesson);

    expect(apiGet).toHaveBeenCalledWith('/admin/groups/group-1/students');
    expect(resources.students).toEqual([
      { id: 'student-2', full_name: 'Второй Студент', subgroup: 2 },
    ]);
  });
});
