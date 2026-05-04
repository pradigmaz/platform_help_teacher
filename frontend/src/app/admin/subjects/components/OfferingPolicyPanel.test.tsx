import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { OfferingPolicyPanel } from './OfferingPolicyPanel';
import { SubjectsAPI, type GroupSubjectOffering, type OfferingPolicy } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  SubjectsAPI: {
    getOfferingPolicy: vi.fn(),
    updateOfferingPolicy: vi.fn(),
  },
}));

const offering: GroupSubjectOffering = {
  id: 'offering-1',
  group_id: 'group-1',
  group_name: 'ИС-21',
  subject_id: 'subject-1',
  subject_name: 'Базы данных',
  semester: '2026-1',
  final_control_type: 'exam',
  exam_question_bank_id: null,
  exam_prep_questions_count: 0,
};

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

describe('OfferingPolicyPanel', () => {
  it('shows a subject context card before lab thresholds', async () => {
    vi.mocked(SubjectsAPI.getOfferingPolicy).mockResolvedValue(policy);

    render(<OfferingPolicyPanel offerings={[offering]} />);

    expect(await screen.findByText('Базы данных')).toBeTruthy();
    expect(screen.getByText('ИС-21')).toBeTruthy();
    expect(screen.getByText('2026-1')).toBeTruthy();
    expect(screen.getByText('настроено')).toBeTruthy();
    expect(screen.getByLabelText('Всего лаб по предмету')).toHaveProperty('value', '8');
  });
});
