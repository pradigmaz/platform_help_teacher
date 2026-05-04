import { describe, expect, it } from 'vitest';
import type { GroupSubjectOffering } from '@/lib/api';
import { getAdminLabOfferingOptions } from './subjectOptions';

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

describe('getAdminLabOfferingOptions', () => {
  it('keeps every group-subject offering as a concrete admin option', () => {
    const offerings = getAdminLabOfferingOptions([
      offering({ id: 'offering-1', group_name: 'ИС1-233-ОТ' }),
      offering({ id: 'offering-2', group_name: 'ИС1-234-ОТ' }),
      offering({
        id: 'offering-3',
        subject_id: 'subject-2',
        subject_name: 'Базы данных',
      }),
    ]);

    expect(offerings).toHaveLength(3);
    expect(offerings.map((option) => option.id)).toContain('offering-1');
    expect(offerings.find((option) => option.id === 'offering-1')).toEqual({
      id: 'offering-1',
      subjectId: 'subject-1',
      subjectName: 'Тестирование информационных систем',
      groupName: 'ИС1-233-ОТ',
      semester: '2026-2',
      label: 'ИС1-233-ОТ / Тестирование информационных систем / 2026-2',
    });
  });
});
