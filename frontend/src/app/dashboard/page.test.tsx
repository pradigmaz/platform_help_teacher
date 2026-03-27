import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  getProfile: vi.fn(),
  getAttendance: vi.fn(),
  getLabs: vi.fn(),
  getAttestationSubjects: vi.fn(),
  getAttestation: vi.fn(),
  toast: {
    error: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: mocks.toast,
}));

vi.mock('@/lib/api', () => ({
  StudentAPI: {
    getProfile: mocks.getProfile,
    getAttendance: mocks.getAttendance,
    getLabs: mocks.getLabs,
    getAttestationSubjects: mocks.getAttestationSubjects,
    getAttestation: mocks.getAttestation,
  },
}));

vi.mock('@/hooks/useSemesterInfo', () => ({
  useSemesterInfo: () => ({
    loading: false,
    academicYear: '2025/2026',
    semester: 'second',
    semesterStartDate: '2026-02-01',
  }),
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
    mocks.getAttendance.mockResolvedValue({
      stats: {
        total_classes: 10,
        present: 9,
        late: 0,
        excused: 0,
        absent: 1,
        attendance_rate: 90,
      },
      records: [],
    });
    mocks.getLabs.mockResolvedValue([
      {
        id: 'lab-1',
        number: 1,
        title: 'ЛР 1',
        subject_id: 'subject-1',
        max_grade: 5,
        is_available: true,
      },
    ]);
    mocks.getAttestation.mockResolvedValue({
      attestation_type: 'second',
      subject_id: 'subject-1',
      total_score: 10,
      grade: '5',
      is_passing: true,
    });
  });

  it('uses dashboard profile context instead of refetching student profile', async () => {
    render(<DashboardOverview />);

    await waitFor(() => {
      expect(screen.getByText('Привет, Иван! 👋')).toBeTruthy();
    });

    expect(mocks.getProfile).not.toHaveBeenCalled();
    expect(mocks.getAttendance).toHaveBeenCalledTimes(1);
    expect(mocks.getLabs).toHaveBeenCalledTimes(1);
  });
});
