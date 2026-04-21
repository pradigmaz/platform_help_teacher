import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import * as React from 'react';

const mocks = vi.hoisted(() => ({
  getExamPrepOfferings: vi.fn(),
  getExamPrep: vi.fn(),
  toast: {
    error: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: mocks.toast,
}));

vi.mock('@/lib/api', () => ({
  StudentAPI: {
    getExamPrepOfferings: mocks.getExamPrepOfferings,
    getExamPrep: mocks.getExamPrep,
  },
}));

vi.mock('@/components/ui/select', () => {
  const SelectContext = React.createContext<{ onValueChange?: (value: string) => void }>({});
  return {
    Select: ({
      children,
      onValueChange,
    }: {
      children: React.ReactNode;
      onValueChange?: (value: string) => void;
    }) => <SelectContext.Provider value={{ onValueChange }}>{children}</SelectContext.Provider>,
    SelectTrigger: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    SelectValue: ({ placeholder }: { placeholder?: string }) => <div>{placeholder}</div>,
    SelectContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    SelectItem: ({ children, value }: { children: React.ReactNode; value: string }) => {
      const { onValueChange } = React.useContext(SelectContext);
      return <button onClick={() => onValueChange?.(value)}>{children}</button>;
    },
  };
});

vi.mock('./components/ExamPrepQuestionList', () => ({
  ExamPrepQuestionList: ({ questions }: { questions: Array<{ id: string }> }) => <div>questions:{questions.length}</div>,
}));

vi.mock('./components/ExamPrepFlashcards', () => ({
  ExamPrepFlashcards: () => <div>flashcards</div>,
}));

vi.mock('./components/ExamPrepQuiz', () => ({
  ExamPrepQuiz: () => <div>quiz</div>,
}));

import ExamPrepPage from './page';

describe('ExamPrepPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders empty state when student has no exam offerings', async () => {
    mocks.getExamPrepOfferings.mockResolvedValue([]);

    render(<ExamPrepPage />);

    await waitFor(() => {
      expect(screen.getByText('Подготовка пока недоступна')).toBeTruthy();
    });
  });

  it('renders an error state when exam offerings load fails', async () => {
    mocks.getExamPrepOfferings.mockRejectedValue(new Error('network failed'));

    render(<ExamPrepPage />);

    await waitFor(() => {
      expect(screen.getByText('Не удалось загрузить экзамены')).toBeTruthy();
      expect(mocks.toast.error).toHaveBeenCalledWith('Не удалось загрузить экзамены для подготовки');
    });

    expect(screen.queryByText('Подготовка пока недоступна')).toBeNull();
  });

  it('renders selected exam payload and default questions tab', async () => {
    mocks.getExamPrepOfferings.mockResolvedValue([
      {
        offering_id: 'offering-1',
        subject_id: 'subject-1',
        subject_name: 'Компьютерные сети',
        semester: '2025-2',
        questions_count: 2,
      },
    ]);
    mocks.getExamPrep.mockResolvedValue({
      offering_id: 'offering-1',
      subject_id: 'subject-1',
      subject_name: 'Компьютерные сети',
      semester: '2025-2',
      questions_count: 2,
      questions: [
        { id: 'q1', prompt: { text: 'Что такое DNS?' } },
        { id: 'q2', prompt: { text: 'Что такое TCP?' } },
      ],
    });

    render(<ExamPrepPage />);

    await waitFor(() => {
      expect(screen.getByText('Компьютерные сети')).toBeTruthy();
    });

    await waitFor(() => {
      expect(mocks.getExamPrep).toHaveBeenCalledWith('offering-1');
      expect(screen.getByText('questions:2')).toBeTruthy();
    });
  });

  it('clears stale questions when switching exam and next payload load fails', async () => {
    mocks.getExamPrepOfferings.mockResolvedValue([
      {
        offering_id: 'offering-1',
        subject_id: 'subject-1',
        subject_name: 'Компьютерные сети',
        semester: '2025-2',
        questions_count: 1,
      },
      {
        offering_id: 'offering-2',
        subject_id: 'subject-2',
        subject_name: 'Теория автоматов',
        semester: '2025-2',
        questions_count: 2,
      },
    ]);
    mocks.getExamPrep.mockResolvedValueOnce({
      offering_id: 'offering-1',
      subject_id: 'subject-1',
      subject_name: 'Компьютерные сети',
      semester: '2025-2',
      questions_count: 1,
      questions: [{ id: 'q1', prompt: { text: 'Что такое DNS?' } }],
    });
    mocks.getExamPrep.mockRejectedValueOnce(new Error('load failed'));

    render(<ExamPrepPage />);

    await waitFor(() => {
      expect(screen.getByText('questions:1')).toBeTruthy();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Теория автоматов' }));

    await waitFor(() => {
      expect(mocks.getExamPrep).toHaveBeenCalledWith('offering-2');
      expect(mocks.toast.error).toHaveBeenCalledWith('Не удалось загрузить вопросы для подготовки');
    });

    expect(screen.queryByText('questions:1')).toBeNull();
    expect(screen.getByText('Не удалось загрузить вопросы')).toBeTruthy();
    expect(screen.queryByText('Вопросы ещё не добавлены')).toBeNull();
  });
});
