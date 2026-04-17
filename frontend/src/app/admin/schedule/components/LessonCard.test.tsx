import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { LessonCard, type LessonData } from './LessonCard';

vi.mock('@/components/notes', () => ({
  NoteButton: () => <button type="button">note</button>,
}));

const baseLesson: LessonData = {
  id: 'lesson-1',
  date: '2026-04-16',
  lesson_number: 1,
  lesson_type: 'lab',
  topic: 'Тестирование информационных систем',
  subject_name: 'Тестирование информационных систем',
  work_number: null,
  subgroup: 1,
  is_cancelled: false,
  ended_early: false,
  group_id: 'group-1',
  group_name: 'ИС1-235-ОТ',
  room: '108Комп/7к',
  summary: null,
};

describe('LessonCard', () => {
  it('renders room with campus suffix from parsed schedule', () => {
    render(<LessonCard lesson={baseLesson} />);

    expect(screen.getByText('ауд. 108Комп/7к')).toBeTruthy();
  });
});
