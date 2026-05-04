import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { SettingsDialog } from './SettingsDialog';

describe('SettingsDialog', () => {
  it('shows legacy lab settings as readonly fallback with inline policy CTA', () => {
    const onOpenOfferingPolicies = vi.fn();
    render(
      <SettingsDialog
        open
        onOpenChange={vi.fn()}
        onOpenOfferingPolicies={onOpenOfferingPolicies}
        settings={{
          labs_count: 12,
          automatic_enabled: true,
          automatic_places: 4,
          grading_scale: '10',
          default_max_grade: 10,
          is_configured: true,
        }}
      />,
    );

    expect(screen.getByText('Legacy-настройки лабораторных')).toBeTruthy();
    expect(screen.getByText('Readonly fallback на время rollout')).toBeTruthy();
    expect(screen.queryByText('Сохранить')).toBeNull();
    expect(screen.getByLabelText('Legacy total лабораторных')).toHaveProperty('readOnly', true);
    fireEvent.click(screen.getByRole('button', { name: 'Настроить по предметам здесь' }));
    expect(onOpenOfferingPolicies).toHaveBeenCalledTimes(1);
  });
});
