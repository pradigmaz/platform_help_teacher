import React, { StrictMode } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  getProfile: vi.fn(),
  getDashboardBootstrap: vi.fn(),
  router: {
    push: vi.fn(),
  },
  toast: {
    error: vi.fn(),
  },
}));

vi.mock('next/navigation', () => ({
  useRouter: () => mocks.router,
  usePathname: () => '/dashboard',
}));

vi.mock('sonner', () => ({
  toast: mocks.toast,
}));

vi.mock('@/lib/api', () => ({
  StudentAPI: {
    getProfile: mocks.getProfile,
    getDashboardBootstrap: mocks.getDashboardBootstrap,
  },
}));

vi.mock('@/components/dashboard/AceternitySidebar', () => ({
  AceternitySidebarLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/dashboard/ImpersonationBanner', () => ({
  ImpersonationBanner: () => null,
}));

vi.mock('@/components/feedback/FeedbackFab', () => ({
  FeedbackFab: () => null,
}));

vi.mock('@/components/ui/skeleton', () => ({
  Skeleton: () => <div>loading</div>,
}));

import DashboardLayout from './layout';

describe('DashboardLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.getDashboardBootstrap.mockResolvedValue({
      profile: {
        id: 'student-1',
        full_name: 'Иванов Иван Иванович',
        username: 'ivanov',
        role: 'student',
        group: {
          id: 'group-1',
          name: 'Группа 101',
          code: '101',
        },
      },
      semester: {
        semester_start_date: '2026-02-01',
        academic_year: 2025,
        semester: 2,
      },
      announcements: [],
      overview: {
        attendance_stats: {
          total_classes: 10,
          present: 9,
          late: 0,
          excused: 0,
          absent: 1,
          attendance_rate: 90,
        },
        labs: [],
        attestation_type: 'second',
        current_attestation: null,
      },
    });
  });

  it('deduplicates dashboard bootstrap under StrictMode', async () => {
    render(
      <StrictMode>
        <DashboardLayout>
          <div>dashboard-child</div>
        </DashboardLayout>
      </StrictMode>,
    );

    await screen.findByText('dashboard-child');

    await waitFor(() => {
      expect(mocks.getDashboardBootstrap).toHaveBeenCalledTimes(1);
    });
  });
});
