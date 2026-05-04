import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { LabsSettingsCard } from './LabsSettingsCard';
import { DEFAULT_FORM_STATE } from './types';

vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));

vi.mock('@/components/ui/slider', () => ({
  Slider: () => <div>slider</div>,
}));

describe('LabsSettingsCard', () => {
  it('keeps legacy lab thresholds readonly and points admins to offering policies', () => {
    render(
      <LabsSettingsCard
        form={DEFAULT_FORM_STATE}
        totalLabsCount={10}
        secondTotalLabsCount={10}
        automaticExtraLabsCount={0}
        onUpdate={vi.fn()}
      />,
    );

    expect(screen.getByText('Пороги лабораторных теперь настраиваются по связке')).toBeTruthy();
    expect(screen.getByRole('link', { name: 'Открыть раздел лабораторных' })).toHaveProperty('href', 'http://localhost:3000/admin/labs');
    expect(screen.getByLabelText('Всего лаб в семестре')).toHaveProperty('readOnly', true);
    expect(screen.getByLabelText('Кол-во для 1-й атт.')).toHaveProperty('readOnly', true);
    expect(screen.getByLabelText('Доп. лаб ко 2-й атт.')).toHaveProperty('readOnly', true);
  });
});
