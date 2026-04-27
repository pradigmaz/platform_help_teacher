import type { ReactElement } from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { TooltipProvider } from '@/components/ui/tooltip';
import { GroupAccordionItem } from './GroupAccordionItem';

const group = {
  id: 'group-1',
  name: 'ПИ-101',
  lesson_id: 'lesson-1',
};

const students = [
  {
    id: 'student-1',
    full_name: 'Жогов Никита Андреевич',
  },
];

function renderWithTooltip(ui: ReactElement) {
  return render(<TooltipProvider delayDuration={0}>{ui}</TooltipProvider>);
}

function openAttendanceMenu() {
  fireEvent.pointerDown(screen.getByLabelText('Выбрать статус посещаемости'), {
    button: 0,
    ctrlKey: false,
  });
}

describe('GroupAccordionItem', () => {
  it('passes direct attendance selection through the grouped lecture row', async () => {
    const onAttendanceChange = vi.fn();

    renderWithTooltip(
      <GroupAccordionItem
        group={group}
        students={students}
        attendance={{}}
        isExpanded
        isLoading={false}
        onToggle={vi.fn()}
        onAttendanceChange={onAttendanceChange}
      />
    );

    openAttendanceMenu();
    fireEvent.click(await screen.findByRole('menuitem', { name: /Отсутствует/i }));

    expect(onAttendanceChange).toHaveBeenCalledWith('student-1', 'ABSENT');
  });
});
