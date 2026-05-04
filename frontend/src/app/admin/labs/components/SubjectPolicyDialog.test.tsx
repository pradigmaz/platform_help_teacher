import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { SubjectsAPI, type OfferingPolicy } from '@/lib/api';
import { SubjectPolicyDialog } from './SubjectPolicyDialog';
import type { AdminLabOfferingOption } from './subjectOptions';

vi.mock('@/lib/api', () => ({
  SubjectsAPI: {
    getOfferingPolicy: vi.fn(),
    updateOfferingPolicy: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

const policy: OfferingPolicy = {
  offering_id: 'offering-1',
  source: 'explicit',
  total_labs: 8,
  labs_required_first: 3,
  labs_required_second_total: 6,
  exam_admission_required_labs: 6,
  automatic_enabled: true,
  automatic_places: 5,
  automatic_required_labs_total: 8,
  second_extra_required: 3,
  automatic_extra_required: 2,
};

function makePolicy(offeringId: string, totalLabs: number): OfferingPolicy {
  return {
    ...policy,
    offering_id: offeringId,
    total_labs: totalLabs,
    labs_required_first: Math.min(3, totalLabs),
    labs_required_second_total: Math.min(6, totalLabs),
    exam_admission_required_labs: Math.min(6, totalLabs),
    automatic_required_labs_total: totalLabs,
  };
}

function deferredPolicy() {
  let resolve!: (value: OfferingPolicy) => void;
  const promise = new Promise<OfferingPolicy>((nextResolve) => {
    resolve = nextResolve;
  });
  return { promise, resolve };
}

const offerings: AdminLabOfferingOption[] = [
  {
    id: 'offering-1',
    subjectId: 'subject-1',
    subjectName: 'Базы данных',
    groupName: 'ИС-21',
    semester: '2026-1',
    label: 'ИС-21 / Базы данных / 2026-1',
  },
  {
    id: 'offering-2',
    subjectId: 'subject-1',
    subjectName: 'Базы данных',
    groupName: 'ИС-22',
    semester: '2026-1',
    label: 'ИС-22 / Базы данных / 2026-1',
  },
];

const twoOfferings: AdminLabOfferingOption[] = [
  offerings[0],
  {
    id: 'offering-3',
    subjectId: 'subject-2',
    subjectName: 'Информатика',
    groupName: 'ИС-23',
    semester: '2026-1',
    label: 'ИС-23 / Информатика / 2026-1',
  },
];

describe('SubjectPolicyDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('saves policy only for the selected concrete offering', async () => {
    vi.mocked(SubjectsAPI.getOfferingPolicy).mockResolvedValue(policy);
    vi.mocked(SubjectsAPI.updateOfferingPolicy).mockResolvedValue(policy);

    render(
      <SubjectPolicyDialog
        open
        onOpenChange={vi.fn()}
        offerings={offerings}
        selectedOfferingId="offering-1"
        onOfferingChange={vi.fn()}
      />,
    );

    expect(await screen.findByLabelText('Всего лаб по предмету')).toHaveProperty('value', '8');
    fireEvent.click(screen.getByRole('button', { name: /Сохранить/ }));

    await waitFor(() => expect(SubjectsAPI.updateOfferingPolicy).toHaveBeenCalledTimes(1));
    expect(SubjectsAPI.updateOfferingPolicy).toHaveBeenCalledWith('offering-1', expect.any(Object));
    expect(SubjectsAPI.updateOfferingPolicy).not.toHaveBeenCalledWith('offering-2', expect.any(Object));
  });

  it('ignores stale policy responses after selected subject changes', async () => {
    const firstRequest = deferredPolicy();
    const secondRequest = deferredPolicy();
    vi.mocked(SubjectsAPI.getOfferingPolicy)
      .mockReturnValueOnce(firstRequest.promise)
      .mockReturnValueOnce(secondRequest.promise);
    vi.mocked(SubjectsAPI.updateOfferingPolicy).mockResolvedValue(makePolicy('offering-3', 5));

    const { rerender } = render(
      <SubjectPolicyDialog
        open
        onOpenChange={vi.fn()}
        offerings={twoOfferings}
        selectedOfferingId="offering-1"
        onOfferingChange={vi.fn()}
      />,
    );

    await waitFor(() => expect(SubjectsAPI.getOfferingPolicy).toHaveBeenCalledWith('offering-1'));
    rerender(
      <SubjectPolicyDialog
        open
        onOpenChange={vi.fn()}
        offerings={twoOfferings}
        selectedOfferingId="offering-3"
        onOfferingChange={vi.fn()}
      />,
    );
    await waitFor(() => expect(SubjectsAPI.getOfferingPolicy).toHaveBeenCalledWith('offering-3'));

    secondRequest.resolve(makePolicy('offering-3', 5));
    expect(await screen.findByLabelText('Всего лаб по предмету')).toHaveProperty('value', '5');
    firstRequest.resolve(makePolicy('offering-1', 12));

    await waitFor(() => expect(screen.getByLabelText('Всего лаб по предмету')).toHaveProperty('value', '5'));
    fireEvent.click(screen.getByRole('button', { name: /Сохранить/ }));

    await waitFor(() => expect(SubjectsAPI.updateOfferingPolicy).toHaveBeenCalledTimes(1));
    expect(SubjectsAPI.updateOfferingPolicy).toHaveBeenCalledWith(
      'offering-3',
      expect.objectContaining({ total_labs: 5 }),
    );
  });
});
