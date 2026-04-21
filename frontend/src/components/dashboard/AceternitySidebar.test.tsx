import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  getExamPrepOfferings: vi.fn(),
  router: {
    push: vi.fn(),
  },
}));

vi.mock('next/navigation', () => ({
  useRouter: () => mocks.router,
  usePathname: () => '/dashboard',
}));

vi.mock('next/link', () => ({
  default: ({ children, href, className, onClick }: { children: React.ReactNode; href: string; className?: string; onClick?: () => void }) => (
    <a href={href} className={className} onClick={onClick}>
      {children}
    </a>
  ),
}));

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => <div {...props}>{children}</div>,
    aside: ({ children, ...props }: React.HTMLAttributes<HTMLElement>) => <aside {...props}>{children}</aside>,
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('@/lib/api/student', () => ({
  StudentAPI: {
    getExamPrepOfferings: mocks.getExamPrepOfferings,
  },
}));

vi.mock('@/lib/api', () => ({
  default: {
    post: vi.fn(),
  },
}));

vi.mock('./NotificationBell', () => ({
  NotificationBell: () => <div>notifications</div>,
}));

vi.mock('./sidebar-brand', () => ({
  SidebarLogo: () => <div>logo</div>,
  SidebarLogoIcon: () => <div>logo-icon</div>,
}));

vi.mock('@/components/ui/animated-theme-toggler', () => ({
  AnimatedThemeToggler: () => <div>theme</div>,
}));

import { AceternitySidebarLayout } from './AceternitySidebar';

describe('AceternitySidebarLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('keeps exam prep navigation visible when the availability request fails', async () => {
    mocks.getExamPrepOfferings.mockRejectedValue(new Error('network failed'));

    const { container } = render(
      <AceternitySidebarLayout
        user={{ name: 'Иванов Иван', username: 'ivanov', group: 'ИС-101' }}
      >
        <div>content</div>
      </AceternitySidebarLayout>,
    );

    fireEvent.mouseEnter(container.querySelector('aside') as HTMLElement);

    await waitFor(() => {
      expect(screen.getAllByText('Подготовка').length).toBeGreaterThan(0);
    });
  });

  it('hides exam prep navigation after a successful empty response', async () => {
    mocks.getExamPrepOfferings.mockResolvedValue([]);

    const { container } = render(
      <AceternitySidebarLayout
        user={{ name: 'Иванов Иван', username: 'ivanov', group: 'ИС-101' }}
      >
        <div>content</div>
      </AceternitySidebarLayout>,
    );

    fireEvent.mouseEnter(container.querySelector('aside') as HTMLElement);

    await waitFor(() => {
      expect(mocks.getExamPrepOfferings).toHaveBeenCalledTimes(1);
    });

    expect(screen.queryByText('Подготовка')).toBeNull();
  });
});
