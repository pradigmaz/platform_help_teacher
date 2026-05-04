import { act, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useStudentLabsPage } from './useStudentLabsPage';

const mocks = vi.hoisted(() => ({
  StudentAPI: {
    getDashboardBootstrap: vi.fn(),
    getAttestationSubjects: vi.fn(),
    getLabs: vi.fn(),
    markLabReady: vi.fn(),
    cancelLabReady: vi.fn(),
  },
  toast: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

vi.mock('@/lib/api', () => ({
  StudentAPI: mocks.StudentAPI,
}));

vi.mock('sonner', () => ({
  toast: mocks.toast,
}));

function Probe() {
  const page = useStudentLabsPage();

  return (
    <div>
      <div>loading:{String(page.loading)}</div>
      <div>must:{String(page.mustChooseSubject)}</div>
      <div>filter:{page.filter}</div>
      <div>labs:{page.labs.map((lab) => lab.title).join(',')}</div>
      <button type="button" onClick={() => page.setFilter('accepted')}>accepted</button>
      <button type="button" onClick={() => page.selectSubject('subject-2')}>subject-2</button>
    </div>
  );
}

function mockBootstrap() {
  mocks.StudentAPI.getDashboardBootstrap.mockResolvedValue({
    overview: {
      attestation_type: 'second',
    },
  });
}

describe('useStudentLabsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockBootstrap();
  });

  it('auto-selects a single subject and loads labs in that scope', async () => {
    mocks.StudentAPI.getAttestationSubjects.mockResolvedValue([{ id: 'subject-1', name: 'Матан' }]);
    mocks.StudentAPI.getLabs.mockResolvedValue([{ id: 'lab-1', title: 'ЛР 1', number: 1, max_grade: 5, is_available: true }]);

    render(<Probe />);

    await waitFor(() => {
      expect(screen.getByText('labs:ЛР 1')).toBeTruthy();
    });

    expect(mocks.StudentAPI.getDashboardBootstrap).toHaveBeenCalledWith();
    expect(mocks.StudentAPI.getAttestationSubjects).toHaveBeenCalledWith('second');
    expect(mocks.StudentAPI.getLabs).toHaveBeenCalledWith({ forceRefresh: undefined, subjectId: 'subject-1' });
  });

  it('requires explicit subject selection when several subjects are available', async () => {
    mocks.StudentAPI.getAttestationSubjects.mockResolvedValue([
      { id: 'subject-1', name: 'Матан' },
      { id: 'subject-2', name: 'Информатика' },
    ]);
    mocks.StudentAPI.getLabs.mockResolvedValue([{ id: 'lab-2', title: 'ЛР 2', number: 2, max_grade: 5, is_available: true }]);

    render(<Probe />);

    await waitFor(() => {
      expect(screen.getByText('must:true')).toBeTruthy();
    });
    expect(mocks.StudentAPI.getLabs).not.toHaveBeenCalled();

    await act(async () => {
      screen.getByText('subject-2').click();
    });

    await waitFor(() => {
      expect(mocks.StudentAPI.getLabs).toHaveBeenCalledWith({ forceRefresh: undefined, subjectId: 'subject-2' });
    });
  });

  it('clears stale filter and labs when subject changes', async () => {
    mocks.StudentAPI.getAttestationSubjects.mockResolvedValue([{ id: 'subject-1', name: 'Матан' }]);
    mocks.StudentAPI.getLabs.mockResolvedValue([{ id: 'lab-1', title: 'ЛР 1', number: 1, max_grade: 5, is_available: true }]);

    render(<Probe />);

    await waitFor(() => {
      expect(screen.getByText('labs:ЛР 1')).toBeTruthy();
    });

    await act(async () => {
      screen.getByText('accepted').click();
      screen.getByText('subject-2').click();
    });

    expect(screen.getByText('filter:all')).toBeTruthy();
  });

  it('does not load unscoped labs when subject context cannot be resolved', async () => {
    mocks.StudentAPI.getAttestationSubjects.mockResolvedValue([]);

    render(<Probe />);

    await waitFor(() => {
      expect(mocks.toast.error).toHaveBeenCalledWith('Не удалось определить предмет для лабораторных');
    });

    expect(mocks.StudentAPI.getLabs).not.toHaveBeenCalled();
  });
});
