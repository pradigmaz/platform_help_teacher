import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { LabSubmissions } from './LabSubmissions';

function makeSubmission(index: number) {
  return {
    lab_id: `lab-${index}`,
    lab_name: `Lab ${index}`,
    lab_number: index,
    grade: 10,
    max_grade: 10,
    submitted_at: `2026-03-${String(index).padStart(2, '0')}T10:00:00Z`,
    is_submitted: true,
    is_late: false,
  };
}

describe('LabSubmissions', () => {
  it('keeps preview stable labs and appends only hidden rows after expand', () => {
    const submissions = Array.from({ length: 6 }, (_, offset) => makeSubmission(offset + 1));

    render(
      <LabSubmissions
        submissions={submissions}
        completed={6}
        total={6}
      />,
    );

    expect(screen.getByText(/Лаб\. 1/i)).toBeTruthy();
    expect(screen.getByText(/Лаб\. 4/i)).toBeTruthy();
    expect(screen.queryByText(/Лаб\. 5/i)).toBeNull();
    expect(screen.queryByText(/Лаб\. 6/i)).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: /Показать/i }));

    expect(screen.getAllByText(/Лаб\. 1/i)).toHaveLength(1);
    expect(screen.getAllByText(/Лаб\. 4/i)).toHaveLength(1);
    expect(screen.getAllByText(/Лаб\. 5/i)).toHaveLength(1);
    expect(screen.getAllByText(/Лаб\. 6/i)).toHaveLength(1);
  });
});
