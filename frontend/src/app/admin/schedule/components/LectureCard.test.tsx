import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import type { GroupedLecture } from '@/components/schedule';
import { LectureCard } from './LectureCard';

const lecture: GroupedLecture = {
  date: '2026-04-16',
  lesson_number: 1,
  subject_id: 'subject-1',
  subject_name: 'Тестирование информационных систем',
  topic: 'Тестирование информационных систем',
  is_cancelled: false,
  ended_early: false,
  room: '119Л/7к',
  groups: [
    {
      id: 'group-1',
      name: 'ИС1-235-ОТ',
      lesson_id: 'lesson-1',
    },
  ],
  summary: null,
};

describe('LectureCard', () => {
  it('renders shared lecture room when it is available', () => {
    render(<LectureCard lecture={lecture} />);

    expect(screen.getByText('ауд. 119Л/7к')).toBeTruthy();
  });
});
