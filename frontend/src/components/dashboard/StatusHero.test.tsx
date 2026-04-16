import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('@/components/ui/magic-card', () => ({
  MagicCard: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/animate-ui/primitives/texts/sliding-number', () => ({
  SlidingNumber: ({ number }: { number: number }) => <span>{number}</span>,
}));

vi.mock('@/components/animate-ui/primitives/effects/effect', () => ({
  Effect: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

vi.mock('./EmptyState', () => ({
  EmptyState: ({ title, description }: { title: string; description?: string }) => (
    <div>
      <div>{title}</div>
      {description ? <div>{description}</div> : null}
    </div>
  ),
}));

import { StatusHero } from './StatusHero';

describe('StatusHero', () => {
  it('renders lab thresholds, remaining work, and automatic places', () => {
    render(
      <StatusHero
        attestation={{
          attestation_type: 'second',
          total_score: 36,
          grade: 'хор',
          is_passing: false,
          max_points: 40,
          min_passing_points: 40,
          lab_progress_plan: {
            total_required: 10,
            first_required: 4,
            second_extra_required: 4,
            second_total_required: 8,
            automatic_extra_required: 2,
            automatic_enabled: true,
            automatic_places: 5,
            completed_count: 3,
            automatic_remaining: 7,
            automatic_queue_position: null,
            automatic_is_winner: null,
            automatic_completion_at: null,
            automatic_reason: null,
            automatic_declined: false,
          },
          breakdown: {
            labs: { score: 20, max: 28, count: 3, required: 8 },
            attendance: { score: 10, max: 12, ratio: 0.9, total_classes: 10, present: 9, late: 0 },
            activity: { score: 1, max: 4, bonus_blocked: false },
          },
        }}
      />,
    );

    expect(screen.getByText('План по лабораторным')).toBeTruthy();
    expect(screen.getByText('1-я аттестация')).toBeTruthy();
    expect(screen.getByText('4 лаб.')).toBeTruthy();
    expect(screen.getByText('Осталось 1')).toBeTruthy();
    expect(screen.getByText('Ещё 4, всего 8')).toBeTruthy();
    expect(screen.getByText('Осталось 5')).toBeTruthy();
    expect(screen.getByText('Ещё 2, всего 10')).toBeTruthy();
    expect(screen.getByText('Осталось 7')).toBeTruthy();
    expect(screen.getByText('Места на автомат')).toBeTruthy();
    expect(screen.getByText('5 мест')).toBeTruthy();
    expect(screen.getByText(/Зачтено:/)).toBeTruthy();
  });

  it('shows disabled automatic mode explicitly', () => {
    render(
      <StatusHero
        attestation={{
          attestation_type: 'first',
          total_score: 22,
          grade: 'уд',
          is_passing: true,
          max_points: 35,
          min_passing_points: 20,
          lab_progress_plan: {
            total_required: 10,
            first_required: 4,
            second_extra_required: 4,
            second_total_required: 8,
            automatic_extra_required: 2,
            automatic_enabled: false,
            automatic_places: 5,
            completed_count: 4,
            automatic_remaining: 6,
            automatic_queue_position: null,
            automatic_is_winner: null,
            automatic_completion_at: null,
            automatic_reason: null,
            automatic_declined: false,
          },
          breakdown: {
            labs: { score: 20, max: 28, count: 4, required: 4 },
            attendance: { score: 10, max: 12, ratio: 1, total_classes: 10, present: 10, late: 0 },
            activity: { score: 1, max: 4, bonus_blocked: false },
          },
        }}
      />,
    );

    expect(screen.getByText('Автоматы')).toBeTruthy();
    expect(screen.getByText('Отключены')).toBeTruthy();
    expect(screen.getByText('Сейчас действует режим без автоматов')).toBeTruthy();
    expect(screen.getByText('Не используются')).toBeTruthy();
  });

  it('explains that automatics are only available for exams', () => {
    render(
      <StatusHero
        attestation={{
          attestation_type: 'second',
          total_score: 36,
          grade: 'хор',
          is_passing: true,
          max_points: 40,
          min_passing_points: 40,
          lab_progress_plan: {
            total_required: 10,
            first_required: 4,
            second_extra_required: 4,
            second_total_required: 8,
            automatic_extra_required: 2,
            automatic_enabled: false,
            automatic_places: 5,
            completed_count: 8,
            automatic_remaining: 2,
            automatic_queue_position: null,
            automatic_is_winner: null,
            automatic_completion_at: null,
            automatic_reason: 'not_exam',
            automatic_declined: false,
          },
          breakdown: {
            labs: { score: 26, max: 28, count: 8, required: 8 },
            attendance: { score: 10, max: 12, ratio: 1, total_classes: 10, present: 10, late: 0 },
            activity: { score: 1, max: 4, bonus_blocked: false },
          },
        }}
      />,
    );

    expect(screen.getByText('Автоматы доступны только по экзамену')).toBeTruthy();
    expect(screen.getByText('Для зачёта и дифзачёта квота не используется')).toBeTruthy();
  });
});
