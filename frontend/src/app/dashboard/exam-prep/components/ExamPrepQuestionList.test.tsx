import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('./ExamPrepContent', () => ({
  ExamPrepContent: ({ value }: { value: { text?: string } | string | null | undefined }) => (
    <div>{typeof value === 'string' ? value : value?.text ?? 'empty'}</div>
  ),
}));

import { ExamPrepQuestionList } from './ExamPrepQuestionList';

describe('ExamPrepQuestionList', () => {
  function QuestionListWithOffering({
    offeringId,
    questions,
  }: {
    offeringId: string;
    questions: Array<{ id: string; prompt: { text: string }; answer: { text: string } }>;
  }) {
    return <ExamPrepQuestionList key={offeringId} questions={questions} />;
  }

  it('clears revealed answers when the offering changes', () => {
    const { rerender } = render(
      <QuestionListWithOffering
        offeringId="offering-1"
        questions={[
          {
            id: 'q1',
            prompt: { text: 'Что такое DNS?' },
            answer: { text: 'Ответ A' },
          },
        ]}
      />,
    );

    fireEvent.click(screen.getByText('Что такое DNS?'));
    fireEvent.click(screen.getByRole('button', { name: 'Показать ответ' }));

    expect(screen.getByText('Ответ A')).toBeTruthy();

    rerender(
      <QuestionListWithOffering
        offeringId="offering-2"
        questions={[
          {
            id: 'q1',
            prompt: { text: 'Что такое маршрутизация?' },
            answer: { text: 'Ответ B' },
          },
        ]}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Вопрос 1 Что такое маршрутизация?' }));

    expect(screen.getByRole('button', { name: 'Показать ответ' })).toBeTruthy();
    expect(screen.queryByText('Ответ B')).toBeNull();
  });
});
