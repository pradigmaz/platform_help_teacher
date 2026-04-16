import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => {
  class MockApiError extends Error {
    status: number;

    constructor(status: number, message: string) {
      super(message);
      this.status = status;
      this.name = 'ApiError';
    }
  }

  return {
    getStudent: vi.fn(),
    router: {
      push: vi.fn(),
    },
    searchParams: new URLSearchParams(),
    MockApiError,
  };
});

vi.mock('next/navigation', () => ({
  useRouter: () => mocks.router,
  useSearchParams: () => mocks.searchParams,
}));

vi.mock('@/lib/api', () => ({
  PublicReportAPI: {
    getStudent: mocks.getStudent,
  },
  ApiError: mocks.MockApiError,
}));

vi.mock('@/lib/utils', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/utils')>();
  return {
    ...actual,
    formatGroupCode: (value: string) => value,
  };
});

vi.mock('../../components/PinDialog', () => ({
  PinDialog: ({ onSuccess }: { onSuccess: () => void }) => (
    <button onClick={onSuccess} type="button">pin-dialog</button>
  ),
}));

vi.mock('./components/ScoreBreakdown', () => ({
  ScoreBreakdown: () => <div>score-breakdown</div>,
}));

vi.mock('./components/ComparisonChart', () => ({
  ComparisonChart: () => <div>comparison-chart</div>,
}));

vi.mock('./components/HeroCard', () => ({
  HeroCard: ({ attestationType }: { attestationType: 'first' | 'second' }) => (
    <div>{`hero-${attestationType}`}</div>
  ),
}));

vi.mock('./components/AttendanceHistory', () => ({
  AttendanceHistory: () => <div>attendance-history</div>,
}));

vi.mock('./components/LabSubmissions', () => ({
  LabSubmissions: () => <div>lab-submissions</div>,
}));

vi.mock('./components/Recommendations', () => ({
  Recommendations: () => <div>recommendations</div>,
}));

vi.mock('@/components/ui/blur-fade', () => ({
  BlurFade: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('../../components/SubjectSelectionCard', () => ({
  SubjectSelectionCard: ({ title }: { title: string }) => <div>{title}</div>,
}));

vi.mock('./components/StudentReportHeader', () => ({
  StudentReportHeader: ({
    attestationType,
    onBack,
  }: {
    attestationType: 'first' | 'second';
    onBack: () => void;
  }) => (
    <button onClick={onBack} type="button">{`header-${attestationType}`}</button>
  ),
}));

vi.mock('./components/AttestationComparisonCards', () => ({
  AttestationComparisonCards: () => <div>attestation-comparison</div>,
}));

import { StudentDetailPageContent } from './page';

function createStudentData() {
  return {
    id: 'student-1',
    name: 'Иван Иванов',
    group_code: 'IS1-231-OT',
    max_points: 100,
    min_passing_points: 60,
    needs_attention: false,
    recommendations: ['Наладить посещаемость'],
    attendance_history: [{ date: '2026-04-01', status: 'present' }],
    lab_submissions: [{ lab_id: 'lab-1', lab_name: 'ЛР 1', lab_number: 1, max_grade: 10, is_submitted: true, is_late: false }],
  };
}

function renderPage() {
  return render(
    <StudentDetailPageContent code="CODE1234" studentId="student-1" />,
  );
}

describe('StudentDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.searchParams = new URLSearchParams();
  });

  it('loads student details with attestation from the URL', async () => {
    mocks.searchParams = new URLSearchParams('attestation=second');
    mocks.getStudent
      .mockResolvedValueOnce(createStudentData())
      .mockResolvedValueOnce(createStudentData());

    renderPage();

    expect(await screen.findByText('score-breakdown')).toBeTruthy();
    expect(mocks.getStudent).toHaveBeenNthCalledWith(
      1,
      'CODE1234',
      'student-1',
      'second',
      undefined,
      expect.any(AbortSignal),
    );
    expect(mocks.getStudent).toHaveBeenNthCalledWith(
      2,
      'CODE1234',
      'student-1',
      'first',
      undefined,
      expect.any(AbortSignal),
    );
    expect(screen.getByText('header-second')).toBeTruthy();
    expect(screen.getByText('attestation-comparison')).toBeTruthy();
    expect(screen.getByText('hero-second')).toBeTruthy();
  });

  it('shows PIN flow for protected reports and retries after success', async () => {
    mocks.getStudent
      .mockRejectedValueOnce(new mocks.MockApiError(401, 'PIN required'))
      .mockResolvedValueOnce(createStudentData());

    renderPage();

    expect(await screen.findByText('pin-dialog')).toBeTruthy();

    fireEvent.click(screen.getByText('pin-dialog'));

    await waitFor(() => {
      expect(mocks.getStudent).toHaveBeenCalledTimes(2);
    });
    expect(await screen.findByText('score-breakdown')).toBeTruthy();
  });

  it('keeps second attestation visible when first-attestation summary fails to load', async () => {
    mocks.searchParams = new URLSearchParams('attestation=second');
    mocks.getStudent
      .mockResolvedValueOnce(createStudentData())
      .mockRejectedValueOnce(new Error('first attestation failed'));

    renderPage();

    expect(await screen.findByText('score-breakdown')).toBeTruthy();
    expect(screen.getByText('hero-second')).toBeTruthy();
    expect(screen.queryByText('attestation-comparison')).toBeNull();
  });

  it('returns to the same attestation from the error state', async () => {
    mocks.searchParams = new URLSearchParams('attestation=second');
    mocks.getStudent.mockRejectedValueOnce(new mocks.MockApiError(404, 'not found'));

    renderPage();

    fireEvent.click(await screen.findByRole('button', { name: 'Вернуться к отчёту' }));

    expect(mocks.router.push).toHaveBeenCalledWith('/report/CODE1234?attestation=second');
  });

  it('passes subject from the URL to the student request and preserves it on back', async () => {
    mocks.searchParams = new URLSearchParams('attestation=second&subject_id=subject-1');
    const data = {
      ...createStudentData(),
      selected_subject_id: 'subject-1',
      available_subjects: [{ id: 'subject-1', name: 'Матан' }],
    };
    mocks.getStudent.mockResolvedValueOnce(data).mockResolvedValueOnce(data);

    renderPage();

    expect(await screen.findByText('score-breakdown')).toBeTruthy();
    expect(mocks.getStudent).toHaveBeenNthCalledWith(
      1,
      'CODE1234',
      'student-1',
      'second',
      'subject-1',
      expect.any(AbortSignal),
    );
    expect(mocks.getStudent).toHaveBeenNthCalledWith(
      2,
      'CODE1234',
      'student-1',
      'first',
      'subject-1',
      expect.any(AbortSignal),
    );

    fireEvent.click(screen.getByText('header-second'));
    expect(mocks.router.push).toHaveBeenCalledWith('/report/CODE1234?attestation=second&subject_id=subject-1');
  });
});
