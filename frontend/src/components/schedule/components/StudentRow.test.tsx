import type { ReactElement } from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { TooltipProvider } from '@/components/ui/tooltip';
import { StudentRow } from './StudentRow';

const baseStudent = {
  id: 'student-1',
  full_name: 'Жогов Никита Андреевич',
};

function renderWithTooltip(ui: ReactElement) {
  return render(<TooltipProvider delayDuration={0}>{ui}</TooltipProvider>);
}

function openAttendanceMenu() {
  fireEvent.pointerDown(screen.getByLabelText('Выбрать статус посещаемости'), {
    button: 0,
    ctrlKey: false,
  });
}

describe('StudentRow', () => {
  it('shows distinct lab grades as a multi-grade badge without conflict', () => {
    const noop = vi.fn();
    renderWithTooltip(
      <StudentRow
        student={baseStudent}
        index={0}
        attendance="PRESENT"
        gradeData={{
          grade: 5,
          work_number: 5,
          has_conflict: false,
          conflict_count: 0,
          grade_items: [
            { grade: 5, work_number: 5 },
            { grade: 5, work_number: 10 },
          ],
        }}
        canHaveGrade
        lessonWorkNumber={null}
        availableWorkNumbers={[5, 10]}
        onAttendanceChange={noop}
        onGradeClick={noop}
        onWorkNumberChange={noop}
      />
    );

    expect(screen.queryByText('Конфликт')).toBeNull();
    expect(screen.getByText('5(5), 5(10)')).toBeTruthy();
  });

  it('allows selecting absent directly from the attendance dropdown', async () => {
    const onAttendanceChange = vi.fn();

    renderWithTooltip(
      <StudentRow
        student={baseStudent}
        index={0}
        attendance={null}
        canHaveGrade={false}
        lessonWorkNumber={null}
        availableWorkNumbers={[]}
        onAttendanceChange={onAttendanceChange}
        onGradeClick={vi.fn()}
        onWorkNumberChange={vi.fn()}
      />
    );

    openAttendanceMenu();
    fireEvent.click(await screen.findByRole('menuitem', { name: /Отсутствует/i }));

    expect(onAttendanceChange).toHaveBeenCalledWith('ABSENT');
  });
});
