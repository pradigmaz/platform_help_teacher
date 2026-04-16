import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { AttendanceHistory } from './AttendanceHistory';

function makeRecord(index: number) {
  return {
    date: `2026-03-${String(index).padStart(2, '0')}`,
    status: index === 8 ? 'absent' : 'present',
    lesson_type: index === 8 ? 'lab' : 'practice',
    lesson_topic: `Topic ${index}`,
  };
}

describe('AttendanceHistory', () => {
  it('keeps preview rows and appends only the hidden tail after expand', () => {
    const history = Array.from({ length: 8 }, (_, offset) => makeRecord(offset + 1));

    render(
      <AttendanceHistory
        history={history}
        stats={{
          present: 7,
          late: 0,
          excused: 0,
          absent: 1,
          total: 8,
          rate: 87.5,
        }}
      />,
    );

    expect(screen.getByText('Topic 8')).toBeTruthy();
    expect(screen.getByText('Лаб. работа')).toBeTruthy();
    expect(screen.getByText('Topic 3')).toBeTruthy();
    expect(screen.queryByText('Topic 2')).toBeNull();
    expect(screen.queryByText('Topic 1')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: /Показать/i }));

    expect(screen.getAllByText('Topic 8')).toHaveLength(1);
    expect(screen.getAllByText('Topic 7')).toHaveLength(1);
    expect(screen.getAllByText('Topic 2')).toHaveLength(1);
    expect(screen.getAllByText('Topic 1')).toHaveLength(1);
  });
});
