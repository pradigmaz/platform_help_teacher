import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  router: {
    push: vi.fn(),
  },
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
  primeAuthFingerprint: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => mocks.router,
}));

vi.mock('sonner', () => ({
  toast: mocks.toast,
}));

vi.mock('@/lib/api', () => ({
  AdminAPI: {
    impersonateUser: vi.fn(),
  },
}));

vi.mock('@/lib/fingerprint/adapter', () => ({
  primeAuthFingerprint: mocks.primeAuthFingerprint,
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button type="button" {...props}>
      {children}
    </button>
  ),
}));

vi.mock('@/components/ui/card', () => ({
  Card: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => <div {...props}>{children}</div>,
  CardContent: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => <div {...props}>{children}</div>,
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, ...props }: React.HTMLAttributes<HTMLSpanElement>) => <span {...props}>{children}</span>,
}));

vi.mock('@/components/ui/alert-dialog', () => ({
  AlertDialog: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AlertDialogAction: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button type="button" {...props}>
      {children}
    </button>
  ),
  AlertDialogCancel: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button type="button" {...props}>
      {children}
    </button>
  ),
  AlertDialogContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AlertDialogDescription: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AlertDialogFooter: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AlertDialogHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AlertDialogTitle: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AlertDialogTrigger: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/ui/border-beam', () => ({
  BorderBeam: () => null,
}));

vi.mock('@/components/ui/sparkles', () => ({
  Sparkles: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('@/components/admin/TransferStudentDialog', () => ({
  TransferStudentDialog: () => <div>transfer-dialog</div>,
}));

import { StudentProfileCard } from './StudentProfileCard';
import type { StudentProfile } from './types';

const activeStudent: StudentProfile = {
  id: 'student-1',
  full_name: 'Alice Student',
  username: 'alice',
  telegram_id: null,
  vk_id: null,
  group_name: 'A-1',
  group_id: 'group-1',
  is_active: true,
  created_at: '2026-03-27T10:00:00Z',
  labs: [],
  stats: {
    labs_total: 0,
    labs_submitted: 0,
    labs_accepted: 0,
    labs_rejected: 0,
    labs_pending: 0,
    labs_overdue: 0,
    points_earned: 0,
    points_max: 0,
    points_percent: 0,
    group_rank: null,
    group_total: null,
    group_percentile: null,
  },
};

describe('StudentProfileCard fingerprint prewarm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('does not prewarm fingerprint on mount', () => {
    render(
      <StudentProfileCard
        student={activeStudent}
        onResetTelegram={vi.fn()}
        resettingTelegram={false}
        onTransferSuccess={vi.fn()}
      />,
    );

    expect(mocks.primeAuthFingerprint).not.toHaveBeenCalled();
  });

  it('prewarms fingerprint only on impersonation intent', () => {
    render(
      <StudentProfileCard
        student={activeStudent}
        onResetTelegram={vi.fn()}
        resettingTelegram={false}
        onTransferSuccess={vi.fn()}
      />,
    );

    const button = screen.getByRole('button', { name: /войти как/i });
    fireEvent.mouseEnter(button);
    fireEvent.focus(button);

    expect(mocks.primeAuthFingerprint).toHaveBeenCalledTimes(2);
  });
});
