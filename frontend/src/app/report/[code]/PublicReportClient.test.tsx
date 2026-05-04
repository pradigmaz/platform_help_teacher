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
    getReport: vi.fn(),
    toastError: vi.fn(),
    router: {
      replace: vi.fn(),
    },
    pathname: '/report/CODE1234',
    searchParams: new URLSearchParams(),
    MockApiError,
  };
});

vi.mock('next/navigation', () => ({
  useRouter: () => mocks.router,
  usePathname: () => mocks.pathname,
  useSearchParams: () => mocks.searchParams,
}));

vi.mock('@/lib/api', () => ({
  PublicReportAPI: {
    getReport: mocks.getReport,
  },
  ApiError: mocks.MockApiError,
}));

vi.mock('@/components/ui/sonner', () => ({
  toast: {
    error: mocks.toastError,
  },
}));

vi.mock('./components/PinDialog', () => ({
  PinDialog: ({ onSuccess }: { onSuccess: () => void }) => (
    <button onClick={onSuccess} type="button">pin-dialog</button>
  ),
}));

vi.mock('./components/ReportHeader', () => ({
  ReportHeader: ({ data }: { data: { attestation_type?: string; group_name?: string } }) => (
    <div>{`header-${data.attestation_type}-${data.group_name}`}</div>
  ),
}));

vi.mock('./components/ReportSummaryCards', () => ({
  ReportSummaryCards: () => <div>summary-cards</div>,
}));

vi.mock('./components/ReportStudentTable', () => ({
  ReportStudentTable: ({ data }: { data: { students: Array<{ id: string }> } }) => (
    <div>{`students-${data.students.length}`}</div>
  ),
}));

vi.mock('./components/ReportToolbar', () => ({
  ReportToolbar: ({
    onAttestationChange,
    onSubjectChange,
    availableSubjects,
  }: {
    onAttestationChange: (value: string) => void;
    onSubjectChange: (value: string) => void;
    availableSubjects: Array<{ id: string; name: string }>;
  }) => (
    <div>
      <button onClick={() => onAttestationChange('second')} type="button">2 аттестация</button>
      {availableSubjects[0] && (
        <button onClick={() => onSubjectChange(availableSubjects[0].id)} type="button">
          {availableSubjects[0].name}
        </button>
      )}
    </div>
  ),
}));

vi.mock('./components/SubjectSelectionCard', () => ({
  SubjectSelectionCard: ({ title }: { title: string }) => <div>{title}</div>,
}));

vi.mock('./components/AttendanceChart', () => ({
  AttendanceChart: () => <div>attendance-chart</div>,
  AttendanceTrend: () => <div>attendance-trend</div>,
}));

vi.mock('./components/LabProgressChart', () => ({
  LabProgressChart: () => <div>lab-progress</div>,
}));

vi.mock('./components/TodayLessonsCard', () => ({
  TodayLessonsCard: () => <div>today-lessons</div>,
}));

vi.mock('./components/PageStates', () => ({
  LoadingSkeleton: () => <div>loading-skeleton</div>,
  ErrorDisplay: ({ error }: { error: string }) => <div>{error}</div>,
}));

vi.mock('@/components/ui/tabs', async () => {
  const ReactModule = await import('react');
  const TabsContext = ReactModule.createContext<{
    value: string;
    onValueChange: (value: string) => void;
  }>({
    value: 'first',
    onValueChange: () => {},
  });

  return {
    Tabs: ({
      value,
      onValueChange,
      children,
    }: {
      value: string;
      onValueChange: (value: string) => void;
      children: React.ReactNode;
    }) => (
      <TabsContext.Provider value={{ value, onValueChange }}>
        <div>{children}</div>
      </TabsContext.Provider>
    ),
    TabsList: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    TabsTrigger: ({
      value,
      disabled,
      children,
    }: {
      value: string;
      disabled?: boolean;
      children: React.ReactNode;
    }) => {
      const context = ReactModule.useContext(TabsContext);
      return (
        <button
          aria-selected={context.value === value}
          disabled={disabled}
          onClick={() => context.onValueChange(value)}
          role="tab"
          type="button"
        >
          {children}
        </button>
      );
    },
  };
});

import { PublicReportClient } from './PublicReportClient';

function createReportData(attestationType: 'first' | 'second') {
  return {
    group_code: 'IS1-231-OT',
    group_name: 'ИС1-231-ОТ',
    report_type: 'full' as const,
    show_names: true,
    show_grades: true,
    show_attendance: true,
    show_rating: true,
    total_students: 1,
    students: [{ id: 'student-1', needs_attention: false }],
    attestation_type: attestationType,
    is_second_available: true,
    requires_subject: false,
    selected_subject_id: null,
    available_subjects: [],
  };
}

describe('PublicReportClient', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.searchParams = new URLSearchParams();
  });

  it('loads once on mount and keeps previous data visible during attestation reload', async () => {
    const firstData = createReportData('first');
    const secondData = createReportData('second');
    let resolveSecondRequest: ((value: unknown) => void) | undefined;

    mocks.getReport
      .mockResolvedValueOnce(firstData)
      .mockReturnValueOnce(new Promise((resolve) => {
        resolveSecondRequest = resolve;
      }));

    render(<PublicReportClient code="CODE1234" />);

    expect(await screen.findByText('header-first-ИС1-231-ОТ')).toBeTruthy();
    expect(mocks.getReport).toHaveBeenCalledTimes(1);
    expect(mocks.getReport).toHaveBeenNthCalledWith(1, 'CODE1234', 'first', undefined, expect.any(AbortSignal));

    fireEvent.click(screen.getByRole('button', { name: '2 аттестация' }));

    await waitFor(() => expect(mocks.getReport).toHaveBeenCalledTimes(2));
    expect(mocks.getReport).toHaveBeenNthCalledWith(2, 'CODE1234', 'second', undefined, expect.any(AbortSignal));
    expect(mocks.router.replace).toHaveBeenCalledWith('/report/CODE1234?attestation=second', { scroll: false });
    expect(screen.getByText('header-first-ИС1-231-ОТ')).toBeTruthy();
    expect(screen.queryByText('loading-skeleton')).toBeNull();

    resolveSecondRequest?.(secondData);

    expect(await screen.findByText('header-second-ИС1-231-ОТ')).toBeTruthy();
    expect(screen.queryByText('Обновляем данные…')).toBeNull();
  });

  it('starts from attestation stored in the URL payload', async () => {
    const secondData = createReportData('second');
    mocks.getReport.mockResolvedValue(secondData);

    render(<PublicReportClient code="CODE1234" initialAttestationType="second" />);

    expect(await screen.findByText('header-second-ИС1-231-ОТ')).toBeTruthy();
    expect(mocks.getReport).toHaveBeenCalledWith('CODE1234', 'second', undefined, expect.any(AbortSignal));
    expect(mocks.router.replace).toHaveBeenCalledWith('/report/CODE1234?attestation=second', { scroll: false });
  });

  it('passes subject from the URL to the report request', async () => {
    mocks.searchParams = new URLSearchParams('attestation=second&subject_id=subject-1');
    const secondData = {
      ...createReportData('second'),
      selected_subject_id: 'subject-1',
      available_subjects: [{ id: 'subject-1', name: 'Матан' }],
    };
    mocks.getReport.mockResolvedValueOnce(secondData);

    render(<PublicReportClient code="CODE1234" initialAttestationType="second" />);

    expect(await screen.findByText('header-second-ИС1-231-ОТ')).toBeTruthy();
    expect(mocks.getReport).toHaveBeenCalledWith(
      'CODE1234',
      'second',
      'subject-1',
      expect.any(AbortSignal),
    );
    expect(mocks.router.replace).not.toHaveBeenCalled();
  });
});
