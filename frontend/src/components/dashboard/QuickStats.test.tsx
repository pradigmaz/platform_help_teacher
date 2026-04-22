import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('next/link', () => ({
  default: ({ children, href }: { children: ReactNode; href: string }) => <a href={href}>{children}</a>,
}));

vi.mock('@/components/ui/metric-card', () => ({
  MetricCard: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/ui/progress', () => ({
  Progress: () => <div>progress</div>,
}));

vi.mock('@/components/animate-ui/primitives/texts/sliding-number', () => ({
  SlidingNumber: ({ number }: { number: number }) => <span>{number}</span>,
}));

vi.mock('@/components/animate-ui/primitives/effects/effect', () => ({
  Effects: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

import { QuickStats } from './QuickStats';

describe('QuickStats', () => {
  it('uses resolved active deadline state instead of raw configured thresholds', () => {
    render(
      <QuickStats
        labs={[
          {
            id: 'lab-expired',
            number: 1,
            title: 'Просроченная',
            max_grade: 5,
            is_available: true,
            deadline_5_lessons: 1,
            deadline_5_status: 'expired',
            lessons_until_deadline_5: null,
            is_accepted: false,
          },
          {
            id: 'lab-active-near',
            number: 2,
            title: 'Активная ближайшая',
            max_grade: 5,
            is_available: true,
            deadline_5_lessons: 5,
            deadline_5_status: 'active',
            lessons_until_deadline_5: 1,
            is_accepted: false,
          },
          {
            id: 'lab-accepted',
            number: 3,
            title: 'Уже зачтена',
            max_grade: 5,
            is_available: true,
            deadline_5_status: 'active',
            lessons_until_deadline_5: 0,
            is_accepted: true,
          },
        ]}
        attendance={null}
        attestation={null}
      />,
    );

    expect(screen.getByText('Активная ближайшая')).toBeTruthy();
    expect(screen.getByText('След. пара')).toBeTruthy();
    expect(screen.queryByText('Просроченная')).toBeNull();
  });

  it('shows empty deadline state when resolved active deadline is absent', () => {
    render(
      <QuickStats
        labs={[
          {
            id: 'lab-raw-only',
            number: 1,
            title: 'Только сырой дедлайн',
            max_grade: 5,
            is_available: true,
            deadline_5_lessons: 1,
            deadline_5_status: null,
            lessons_until_deadline_5: null,
            is_accepted: false,
          },
        ]}
        attendance={null}
        attestation={null}
      />,
    );

    expect(screen.getByText('Нет активных дедлайнов')).toBeTruthy();
  });
});
