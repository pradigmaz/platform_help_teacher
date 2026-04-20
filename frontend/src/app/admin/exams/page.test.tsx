import * as React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  useAdminExamOfferings: vi.fn(),
  refetch: vi.fn(),
}));

vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));

vi.mock('@/components/admin/useAdminExamOfferings', () => ({
  useAdminExamOfferings: mocks.useAdminExamOfferings,
}));

vi.mock('@/components/ui/blur-fade', () => ({
  BlurFade: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('@/app/admin/subjects/components/ExamPrepEditorSheet', () => ({
  ExamPrepEditorSheet: ({ open }: { open: boolean }) => (open ? <div>editor open</div> : null),
}));

import AdminExamsPage from './page';

describe('AdminExamsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders empty state when there are no exam offerings', () => {
    mocks.useAdminExamOfferings.mockReturnValue({
      examOfferings: [],
      isLoading: false,
      error: false,
      refetch: mocks.refetch,
    });

    render(<AdminExamsPage />);

    expect(screen.getByText('Экзаменов пока нет')).toBeTruthy();
    expect(screen.getByText('Открыть предметы групп')).toBeTruthy();
  });

  it('renders exam offerings and opens editor sheet', async () => {
    mocks.useAdminExamOfferings.mockReturnValue({
      examOfferings: [
        {
          id: 'offering-1',
          group_id: 'group-1',
          group_name: 'ИВТ-31',
          subject_id: 'subject-1',
          subject_name: 'Компьютерные сети',
          semester: '2025-2',
          final_control_type: 'exam',
          exam_prep_questions_count: 3,
        },
      ],
      isLoading: false,
      error: false,
      refetch: mocks.refetch,
    });

    render(<AdminExamsPage />);

    expect(screen.getByText('Компьютерные сети')).toBeTruthy();
    expect(screen.getByText('ИВТ-31')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Открыть вопросы' }));

    await waitFor(() => {
      expect(screen.getByText('editor open')).toBeTruthy();
    });
  });
});
