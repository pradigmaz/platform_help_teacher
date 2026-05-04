import { describe, expect, it } from 'vitest';
import type { GroupSubjectOffering } from '@/lib/api';
import { getAdminLabSubjectOptions } from './subjectOptions';

function offering(overrides: Partial<GroupSubjectOffering>): GroupSubjectOffering {
  return {
    id: 'offering-1',
    group_id: 'group-1',
    group_name: 'ИС1-233-ОТ',
    subject_id: 'subject-1',
    subject_name: 'Тестирование информационных систем',
    semester: '2026-2',
    final_control_type: 'exam',
    exam_question_bank_id: null,
    exam_prep_questions_count: 0,
    ...overrides,
  };
}

describe('getAdminLabSubjectOptions', () => {
  it('deduplicates offerings into subjects and keeps concrete offering options', () => {
    const subjects = getAdminLabSubjectOptions([
      offering({ id: 'offering-1', group_name: 'ИС1-233-ОТ' }),
      offering({ id: 'offering-2', group_name: 'ИС1-234-ОТ' }),
      offering({
        id: 'offering-3',
        subject_id: 'subject-2',
        subject_name: 'Базы данных',
      }),
    ]);

    expect(subjects).toHaveLength(2);
    expect(subjects.find((subject) => subject.id === 'subject-1')).toEqual({
      id: 'subject-1',
      name: 'Тестирование информационных систем',
      offeringIds: ['offering-1', 'offering-2'],
      offerings: [
        { id: 'offering-1', subjectId: 'subject-1', label: 'ИС1-233-ОТ / 2026-2' },
        { id: 'offering-2', subjectId: 'subject-1', label: 'ИС1-234-ОТ / 2026-2' },
      ],
    });
  });
});
