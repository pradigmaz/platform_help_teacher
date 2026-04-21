import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import * as React from 'react';

const mocks = vi.hoisted(() => ({
  getOfferingContext: vi.fn(),
  createBank: vi.fn(),
  assignBank: vi.fn(),
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
    getOfferingContext: mocks.getOfferingContext,
    createBank: mocks.createBank,
    assignBank: mocks.assignBank,
  },
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => <button {...props}>{children}</button>,
}));

vi.mock('@/components/ui/sheet', () => ({
  Sheet: ({ children, open }: { children: React.ReactNode; open: boolean }) => (open ? <div>{children}</div> : null),
  SheetContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SheetDescription: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SheetHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SheetTitle: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

import { ExamOfferingContextSheet } from './ExamOfferingContextSheet';

describe('ExamOfferingContextSheet', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('clears stale offering context when the next load fails', async () => {
    mocks.getOfferingContext
      .mockResolvedValueOnce({
        offering: {
          offering_id: 'offering-a',
          group_id: 'group-a',
          group_name: 'ИВТ-31',
          subject_id: 'subject-1',
          subject_name: 'Компьютерные сети',
          semester: '2025-2',
          questions_count: 0,
        },
        bank: null,
        compatible_banks: [],
      })
      .mockRejectedValueOnce(new Error('load failed'));

    const { rerender } = render(
      <ExamOfferingContextSheet
        open={true}
        offeringId="offering-a"
        onOpenChange={() => undefined}
        onBankOpened={() => undefined}
        onChanged={() => undefined}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText('ИВТ-31')).toBeTruthy();
      expect(screen.getByRole('button', { name: 'Создать новый банк' })).toBeTruthy();
    });

    rerender(
      <ExamOfferingContextSheet
        open={true}
        offeringId="offering-b"
        onOpenChange={() => undefined}
        onBankOpened={() => undefined}
        onChanged={() => undefined}
      />,
    );

    await waitFor(() => {
      expect(mocks.toast.error).toHaveBeenCalledWith('Не удалось загрузить контекст экзамена');
    });

    expect(screen.queryByText('ИВТ-31')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Создать новый банк' })).toBeNull();
  });
});
