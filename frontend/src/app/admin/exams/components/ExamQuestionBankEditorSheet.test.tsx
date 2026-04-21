import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import * as React from 'react';

const mocks = vi.hoisted(() => ({
  getBank: vi.fn(),
  updateBank: vi.fn(),
  toast: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: mocks.toast,
}));

vi.mock('@/lib/api', () => ({
  ExamBanksAPI: {
    getBank: mocks.getBank,
    updateBank: mocks.updateBank,
  },
}));

vi.mock('@/components/lectures/LectureEditor', () => ({
  default: () => <div data-testid="lecture-editor" />,
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => <button {...props}>{children}</button>,
}));

vi.mock('@/components/ui/scroll-area', () => ({
  ScrollArea: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/ui/sheet', () => ({
  Sheet: ({ children, open }: { children: React.ReactNode; open: boolean }) => (open ? <div>{children}</div> : null),
  SheetContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SheetDescription: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SheetHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SheetTitle: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

import { ExamQuestionBankEditorSheet } from './ExamQuestionBankEditorSheet';

describe('ExamQuestionBankEditorSheet', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('clears stale bank state when next bank load fails', async () => {
    mocks.getBank
      .mockResolvedValueOnce({
        bank_id: 'bank-a',
        subject_id: 'subject-1',
        subject_name: 'Компьютерные сети',
        semester: '2025-2',
        questions_count: 1,
        offerings: [],
        questions: [{ id: 'q1', prompt: { text: 'Что такое DNS?' } }],
      })
      .mockRejectedValueOnce(new Error('load failed'));

    const { rerender } = render(
      <ExamQuestionBankEditorSheet
        open={true}
        bankId="bank-a"
        onOpenChange={() => undefined}
        onSaved={() => undefined}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText('Банк вопросов: Компьютерные сети')).toBeTruthy();
    });

    rerender(
      <ExamQuestionBankEditorSheet
        open={true}
        bankId="bank-b"
        onOpenChange={() => undefined}
        onSaved={() => undefined}
      />,
    );

    await waitFor(() => {
      expect(mocks.toast.error).toHaveBeenCalledWith('Не удалось загрузить банк вопросов');
    });

    expect(screen.queryByText('Банк вопросов: Компьютерные сети')).toBeNull();
    expect(screen.getByRole('button', { name: 'Сохранить' }).hasAttribute('disabled')).toBe(true);
  });
});
