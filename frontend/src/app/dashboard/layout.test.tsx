import React, { StrictMode } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  getProfile: vi.fn(),
  router: {
    push: vi.fn(),
  },
  toast: {
    error: vi.fn(),
  },
}));

vi.mock('next/navigation', () => ({
  useRouter: () => mocks.router,
}));

vi.mock('sonner', () => ({
  toast: mocks.toast,
}));

vi.mock('@/lib/api', () => ({
  StudentAPI: {
    getProfile: mocks.getProfile,
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
    mocks.getProfile.mockResolvedValue({
      id: 'student-1',
      full_name: 'Иванов Иван Иванович',
      username: 'ivanov',
      role: 'student',
      group: {
        id: 'group-1',
        name: 'Группа 101',
        code: '101',
      },
    });
  });

  it('deduplicates profile bootstrap under StrictMode', async () => {
    render(
      <StrictMode>
        <DashboardLayout>
          <div>dashboard-child</div>
        </DashboardLayout>
      </StrictMode>,
    );

    await screen.findByText('dashboard-child');

    await waitFor(() => {
      expect(mocks.getProfile).toHaveBeenCalledTimes(1);
    });
  });
});
