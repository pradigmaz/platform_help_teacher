import { describe, expect, it } from 'vitest';

import { resolveSubjectSelection } from './useJournalData';

describe('resolveSubjectSelection', () => {
  it('selects the first available subject instead of leaving journal in all-subject mode', () => {
    expect(
      resolveSubjectSelection('all', [
        { id: 'subject-1', name: 'Тестирование' },
        { id: 'subject-2', name: 'Разработка' },
      ])
    ).toBe('subject-1');
  });

  it('keeps a selected subject when it still belongs to the semester', () => {
    expect(
      resolveSubjectSelection('subject-2', [
        { id: 'subject-1', name: 'Тестирование' },
        { id: 'subject-2', name: 'Разработка' },
      ])
    ).toBe('subject-2');
  });
});
