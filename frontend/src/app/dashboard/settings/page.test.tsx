import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  relinkTelegram: vi.fn(),
  linkVk: vi.fn(),
  getProfile: vi.fn(),
  setTheme: vi.fn(),
}));

vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
  },
}));

vi.mock('@/lib/api', () => ({
  StudentAPI: {
    relinkTelegram: mocks.relinkTelegram,
    linkVk: mocks.linkVk,
    getProfile: mocks.getProfile,
  },
}));

vi.mock('../DashboardProfileProvider', () => ({
  useDashboardProfile: () => ({
    profile: {
      id: 'student-1',
      full_name: 'Иванов Иван Иванович',
      username: 'ivanov',
      role: 'student',
      telegram_id: 123,
      vk_id: 456,
      group: {
        id: 'group-1',
        name: 'Группа 101',
        code: '101',
      },
    },
    isLoading: false,
  }),
}));

vi.mock('next-themes', () => ({
  useTheme: () => ({
    theme: 'light',
    setTheme: mocks.setTheme,
  }),
}));

vi.mock('motion/react', () => ({
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('@/components/ui/text-generate-effect', () => ({
  TextGenerateEffect: ({ words }: { words: string }) => <div>{words}</div>,
}));

vi.mock('@/components/ui/skeleton', () => ({
  Skeleton: () => <div>loading</div>,
}));

vi.mock('@/components/ui/tabs', () => ({
  Tabs: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  TabsList: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  TabsTrigger: ({ children }: { children: React.ReactNode }) => <button type="button">{children}</button>,
  TabsContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('./components', () => ({
  ProfileTab: ({ profile }: { profile: { full_name: string } }) => <div>{profile.full_name}</div>,
  NotificationsTab: () => <div>notifications-tab</div>,
  AppearanceTab: () => <div>appearance-tab</div>,
  SecurityTab: () => <div>security-tab</div>,
}));

import SettingsPage from './page';

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('uses dashboard profile context instead of refetching student profile', () => {
    render(<SettingsPage />);

    expect(screen.getByText('Настройки')).toBeTruthy();
    expect(screen.getByText('Иванов Иван Иванович')).toBeTruthy();
    expect(mocks.getProfile).not.toHaveBeenCalled();
  });
});
