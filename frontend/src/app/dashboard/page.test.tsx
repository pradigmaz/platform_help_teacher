import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  toast: {
    error: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: mocks.toast,
}));

vi.mock('./DashboardProfileProvider', () => ({
  useDashboardProfile: () => ({
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
    bootstrap: {
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
        labs: [
          {
            id: 'lab-1',
            number: 1,
            title: 'ЛР 1',
            subject_id: 'subject-1',
            max_grade: 5,
            is_available: true,
          },
        ],
        attestation_type: 'second',
        current_attestation: {
          attestation_type: 'second',
          subject_id: 'subject-1',
          total_score: 10,
          grade: '5',
          is_passing: true,
        },
      },
    },
    isLoading: false,
  }),
}));

vi.mock('@/components/animate-ui/primitives/effects/effect', () => ({
  Effect: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('@/components/ui/skeleton', () => ({
  Skeleton: () => <div>loading</div>,
}));

vi.mock('@/components/dashboard', () => ({
  StatusHero: () => <div>status-hero</div>,
  QuickStats: () => <div>quick-stats</div>,
  DeadlinesList: () => <div>deadlines-list</div>,
}));

import DashboardOverview from './page';

describe('DashboardOverview', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders overview from dashboard bootstrap context', async () => {
    render(<DashboardOverview />);

    await waitFor(() => {
      expect(screen.getByText('Привет, Иван! 👋')).toBeTruthy();
    });
  });
});
