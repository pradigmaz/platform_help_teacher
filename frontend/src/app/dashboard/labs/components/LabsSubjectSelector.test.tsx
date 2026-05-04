import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { LabsSubjectSelector } from './LabsSubjectSelector';

describe('LabsSubjectSelector', () => {
  it('shows the current subject even when the context auto-selects a single subject', () => {
    render(
      <LabsSubjectSelector
        subjects={[{ id: 'subject-1', name: 'Матан' }]}
        selectedSubject={{ id: 'subject-1', name: 'Матан' }}
        selectedSubjectId="subject-1"
        onSelectSubject={() => {}}
      />,
    );

    expect(screen.getByText('Текущий предмет')).toBeTruthy();
    expect(screen.getByText('Матан')).toBeTruthy();
    expect(screen.getByText('Этот предмет выбран автоматически. Ниже показаны лабораторные только по нему.')).toBeTruthy();
  });
});

