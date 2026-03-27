import { act, render, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => {
  const readIds = new Set<string>();

  return {
    getAnnouncements: vi.fn(),
    markAnnouncementAsRead: vi.fn((id: string) => {
      readIds.add(id);
    }),
    getReadAnnouncementIds: vi.fn(() => new Set(readIds)),
    clearAllAnnouncements: vi.fn(() => {
      readIds.clear();
    }),
    resetReadIds: () => {
      readIds.clear();
    },
  };
});

vi.mock('@/lib/api/announcements', () => ({
  AnnouncementsAPI: {
    getAnnouncements: mocks.getAnnouncements,
  },
  getReadAnnouncementIds: mocks.getReadAnnouncementIds,
  markAnnouncementAsRead: mocks.markAnnouncementAsRead,
  getUnreadCount: (announcements: Array<{ id: string }>) =>
    announcements.filter((announcement) => !mocks.getReadAnnouncementIds().has(announcement.id)).length,
  clearAllAnnouncements: mocks.clearAllAnnouncements,
}));

vi.mock('@/components/ui/popover', () => ({
  Popover: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  PopoverTrigger: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  PopoverContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/ui/scroll-area', () => ({
  ScrollArea: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button type="button" {...props}>
      {children}
    </button>
  ),
}));

vi.mock('react-markdown', () => ({
  default: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

import { NotificationBell } from './NotificationBell';
import { resetNotificationBellStoreForTests } from './notification-bell-store';

describe('NotificationBell', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    mocks.resetReadIds();
    resetNotificationBellStoreForTests();
    mocks.getAnnouncements.mockResolvedValue([
      {
        id: 'announcement-1',
        title: 'Новость',
        content: 'Контент',
        is_draft: false,
        published_at: '2026-03-27T10:00:00Z',
        created_at: '2026-03-27T10:00:00Z',
      },
    ]);
  });

  afterEach(() => {
    resetNotificationBellStoreForTests();
    vi.useRealTimers();
  });

  it('shares one initial request and one polling loop across multiple mounts', async () => {
    render(
      <>
        <NotificationBell />
        <NotificationBell />
      </>,
    );

    await act(async () => {
      await Promise.resolve();
    });
    expect(mocks.getAnnouncements).toHaveBeenCalledTimes(1);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(5 * 60 * 1000);
    });

    expect(mocks.getAnnouncements).toHaveBeenCalledTimes(2);
  });

  it('refreshes announcements on a fresh remount after all subscribers are gone', async () => {
    const firstRender = render(<NotificationBell />);

    await act(async () => {
      await Promise.resolve();
    });
    expect(mocks.getAnnouncements).toHaveBeenCalledTimes(1);

    firstRender.unmount();

    render(<NotificationBell />);

    await act(async () => {
      await Promise.resolve();
    });
    expect(mocks.getAnnouncements).toHaveBeenCalledTimes(2);
  });
});
