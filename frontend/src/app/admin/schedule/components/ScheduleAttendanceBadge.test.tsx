import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { TooltipProvider } from '@/components/ui/tooltip';
import { ScheduleAttendanceBadge, getAttendanceSummaryPresentation } from './ScheduleAttendanceBadge';

describe('getAttendanceSummaryPresentation', () => {
  it('hides hidden and not_applicable states', () => {
    expect(
      getAttendanceSummaryPresentation({
        state: 'hidden',
        marked_count: 0,
        expected_count: 10,
        is_past: false,
      })
    ).toBeNull();

    expect(
      getAttendanceSummaryPresentation({
        state: 'not_applicable',
        marked_count: 0,
        expected_count: 0,
        is_past: true,
      })
    ).toBeNull();
  });

  it('returns presentation metadata for visible states', () => {
    expect(
      getAttendanceSummaryPresentation({
        state: 'partial',
        marked_count: 3,
        expected_count: 5,
        is_past: true,
      })
    )?.toMatchObject({
      badge_label: 'Частично',
      tooltip: 'Посещаемость выставлена частично',
    });
  });
});

describe('ScheduleAttendanceBadge', () => {
  it('does not render anything for hidden state', () => {
    const { container } = render(
      <ScheduleAttendanceBadge
        summary={{
          state: 'hidden',
          marked_count: 0,
          expected_count: 5,
          is_past: false,
        }}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('renders visible state with accessible counts label', () => {
    render(
      <TooltipProvider>
        <ScheduleAttendanceBadge
          summary={{
            state: 'complete',
            marked_count: 5,
            expected_count: 5,
            is_past: true,
          }}
        />
      </TooltipProvider>
    );

    const badge = screen.getByLabelText('Посещаемость выставлена (5/5)');
    expect(badge.getAttribute('title')).toBe('Посещаемость выставлена (5/5)');
    expect(badge.textContent).toContain('Готово');
    expect(badge.textContent).toContain('5/5');
  });
});
