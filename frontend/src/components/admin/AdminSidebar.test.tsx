import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('next/navigation', () => ({
  usePathname: () => '/admin',
}));

vi.mock('./useAdminFeedbackCount', () => ({
  useAdminFeedbackCount: () => 0,
}));

vi.mock('./AdminSidebarNav', () => ({
  AdminSidebarNav: () => <nav>Smoke nav</nav>,
}));

import { MobileSidebarTrigger } from './AdminSidebar';

describe('MobileSidebarTrigger', () => {
  it('renders an accessible sheet description for the admin navigation dialog', async () => {
    render(<MobileSidebarTrigger />);

    fireEvent.click(screen.getByRole('button', { name: 'Открыть меню' }));

    expect(await screen.findByText('Навигация администратора')).toBeTruthy();
    expect(screen.getByText('Основные разделы и быстрые переходы по административным страницам.')).toBeTruthy();
    expect(screen.getByText('Smoke nav')).toBeTruthy();
  });
});
