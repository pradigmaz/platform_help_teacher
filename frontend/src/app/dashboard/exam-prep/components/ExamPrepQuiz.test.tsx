import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('./ExamPrepContent', () => ({
  ExamPrepContent: ({ value }: { value: { text?: string } | string | null | undefined }) => (
    <div>{typeof value === 'string' ? value : value?.text ?? 'empty'}</div>
  ),
}));

import { ExamPrepQuiz } from './ExamPrepQuiz';

describe('ExamPrepQuiz', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('requeues the current question when student marks it for repetition', () => {
    vi.spyOn(Math, 'random').mockReturnValue(0.4);

    render(
      <ExamPrepQuiz
        questions={[
          {
            id: 'q1',
            prompt: { text: 'Что такое DNS?' },
            answer: { text: 'Система доменных имён' },
          },
        ]}
      />,
    );

    expect(screen.getByText('Вопрос 1 из 1')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Повторить' }));

    expect(screen.getByText('Вопрос 2 из 2')).toBeTruthy();
    expect(screen.queryByText('Сессия завершена')).toBeNull();
    expect(screen.getByText('Повторить: 1')).toBeTruthy();
  });
});
