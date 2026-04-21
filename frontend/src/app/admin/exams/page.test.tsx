import * as React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  listGroups: vi.fn(),
  createBank: vi.fn(),
  replace: vi.fn(),
  searchParams: new URLSearchParams(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace: mocks.replace }),
  useSearchParams: () => mocks.searchParams,
}));

vi.mock('@/components/ui/blur-fade', () => ({
  BlurFade: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('@/lib/api', async () => {
  const actual = await vi.importActual<typeof import('@/lib/api')>('@/lib/api');
  return {
    ...actual,
    ExamBanksAPI: {
      listGroups: mocks.listGroups,
      createBank: mocks.createBank,
    },
  };
});

vi.mock('./components/ExamQuestionBankEditorSheet', () => ({
  ExamQuestionBankEditorSheet: ({ open }: { open: boolean }) => (open ? <div>editor open</div> : null),
}));

vi.mock('./components/ExamBankAssignmentDialog', () => ({
  ExamBankAssignmentDialog: () => null,
}));

vi.mock('./components/ExamBankSplitDialog', () => ({
  ExamBankSplitDialog: () => null,
}));

vi.mock('./components/ExamOfferingContextSheet', () => ({
  ExamOfferingContextSheet: ({ open }: { open: boolean }) => (open ? <div>offering context</div> : null),
}));

import AdminExamsPage from './page';

describe('AdminExamsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.searchParams = new URLSearchParams();
  });

  it('renders empty state when there are no exam groups', async () => {
    mocks.listGroups.mockResolvedValue([]);

    render(<AdminExamsPage />);

    await waitFor(() => {
      expect(screen.getByText('Экзаменов пока нет')).toBeTruthy();
    });
  });

  it('renders grouped banks and opens editor for a bank', async () => {
    mocks.listGroups.mockResolvedValue([
      {
        subject_id: 'subject-1',
        subject_name: 'Компьютерные сети',
        semester: '2025-2',
        banks: [
          {
            bank_id: 'bank-1',
            subject_id: 'subject-1',
            subject_name: 'Компьютерные сети',
            semester: '2025-2',
            questions_count: 3,
            offerings: [
              {
                offering_id: 'offering-1',
                group_id: 'group-1',
                group_name: 'ИВТ-31',
                subject_id: 'subject-1',
                subject_name: 'Компьютерные сети',
                semester: '2025-2',
                questions_count: 3,
              },
            ],
          },
        ],
        unassigned_offerings: [],
      },
    ]);

    render(<AdminExamsPage />);

    await waitFor(() => {
      expect(screen.getByText('Компьютерные сети')).toBeTruthy();
    });

    expect(screen.getByText('ИВТ-31')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Редактировать банк' }));

    await waitFor(() => {
      expect(screen.getByText('editor open')).toBeTruthy();
    });
  });

  it('opens offering context from query string', async () => {
    mocks.searchParams = new URLSearchParams('offering=offering-1');
    mocks.listGroups.mockResolvedValue([
      {
        subject_id: 'subject-1',
        subject_name: 'Компьютерные сети',
        semester: '2025-2',
        banks: [],
        unassigned_offerings: [],
      },
    ]);

    render(<AdminExamsPage />);

    await waitFor(() => {
      expect(screen.getByText('offering context')).toBeTruthy();
    });
  });
});
