import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { StudentRow } from './StudentRow';

vi.mock('@/components/notes', () => ({
  NoteButton: () => <button type="button" aria-label="note" />,
}));

const baseStudent = {
  id: 'student-1',
  full_name: 'Жогов Никита Андреевич',
};

const noop = vi.fn();

describe('StudentRow', () => {
  it('shows distinct lab grades as a multi-grade badge without conflict', () => {
    render(
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
        onAttendanceClick={noop}
        onGradeClick={noop}
        onWorkNumberChange={noop}
      />
    );

    expect(screen.queryByText('Конфликт')).toBeNull();
    expect(screen.getByText('5(5), 5(10)')).toBeTruthy();
  });
});
