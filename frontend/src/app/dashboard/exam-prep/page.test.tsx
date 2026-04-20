import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

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
});
