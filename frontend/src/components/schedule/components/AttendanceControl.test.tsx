import type { ReactElement } from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { TooltipProvider } from '@/components/ui/tooltip';
import { AttendanceControl } from './AttendanceControl';

function renderWithTooltip(ui: ReactElement) {
  return render(<TooltipProvider delayDuration={0}>{ui}</TooltipProvider>);
}

function openAttendanceMenu() {
  fireEvent.pointerDown(screen.getByLabelText('Выбрать статус посещаемости'), {
    button: 0,
    ctrlKey: false,
  });
}

describe('AttendanceControl', () => {
  it('allows choosing absent directly from the dropdown menu', async () => {
    const onStatusChange = vi.fn();

    renderWithTooltip(<AttendanceControl status="PRESENT" onStatusChange={onStatusChange} />);

    openAttendanceMenu();
    fireEvent.click(await screen.findByRole('menuitem', { name: /Отсутствует/i }));

    expect(onStatusChange).toHaveBeenCalledWith('ABSENT');
  });

  it('allows resetting the current status from the dropdown menu', async () => {
    const onStatusChange = vi.fn();

    renderWithTooltip(<AttendanceControl status="ABSENT" onStatusChange={onStatusChange} />);

    openAttendanceMenu();
    fireEvent.click(await screen.findByRole('menuitem', { name: /Сбросить/i }));

    expect(onStatusChange).toHaveBeenCalledWith(null);
  });
});
