'use client';

import * as React from 'react';
import { usePathname } from 'next/navigation';
import { StudentAPI, type StudentDashboardBootstrap, type StudentProfile } from '@/lib/api';
import { hydrateNotificationBellStore } from '@/components/dashboard/notification-bell-store';

interface DashboardProfileContextValue {
  profile: StudentProfile | null;
  bootstrap: StudentDashboardBootstrap | null;
  isLoading: boolean;
  error: unknown;
}

const DashboardProfileContext = React.createContext<DashboardProfileContextValue | null>(null);

let inFlightProfileRequest: Promise<StudentProfile> | null = null;
let inFlightDashboardBootstrapRequest: Promise<StudentDashboardBootstrap> | null = null;

async function loadDashboardProfile() {
  if (!inFlightProfileRequest) {
    inFlightProfileRequest = StudentAPI.getProfile().finally(() => {
      inFlightProfileRequest = null;
    });
  }

  return inFlightProfileRequest;
}

async function loadDashboardBootstrap() {
  if (!inFlightDashboardBootstrapRequest) {
    inFlightDashboardBootstrapRequest = StudentAPI.getDashboardBootstrap().finally(() => {
      inFlightDashboardBootstrapRequest = null;
    });
  }

  return inFlightDashboardBootstrapRequest;
}

export function DashboardProfileProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [profile, setProfile] = React.useState<StudentProfile | null>(null);
  const [bootstrap, setBootstrap] = React.useState<StudentDashboardBootstrap | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<unknown>(null);

  React.useEffect(() => {
    let cancelled = false;
    const isDashboardOverviewRoute = pathname === '/dashboard';

    if (isDashboardOverviewRoute && bootstrap) {
      setIsLoading(false);
      setError(null);
      return () => {
        cancelled = true;
      };
    }

    const loadData = async () => {
      try {
        if (isDashboardOverviewRoute) {
          const nextBootstrap = await loadDashboardBootstrap();
          if (!cancelled) {
            hydrateNotificationBellStore(nextBootstrap.announcements);
            setBootstrap(nextBootstrap);
            setProfile(nextBootstrap.profile);
            setError(null);
          }
          return;
        }

        if (profile) {
          if (!cancelled) {
            setError(null);
          }
          return;
        }

        const nextProfile = await loadDashboardProfile();
        if (!cancelled) {
          setProfile(nextProfile);
          setBootstrap((currentBootstrap) =>
            currentBootstrap?.profile.id === nextProfile.id ? currentBootstrap : null,
          );
          setError(null);
        }
      } catch (nextError) {
        if (!cancelled) {
          setProfile(null);
          setBootstrap(null);
          setError(nextError);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void loadData();

    return () => {
      cancelled = true;
    };
  }, [pathname, profile, bootstrap]);

  const value = React.useMemo(
    () => ({
      profile,
      bootstrap,
      isLoading,
      error,
    }),
    [profile, bootstrap, isLoading, error],
  );

  return <DashboardProfileContext.Provider value={value}>{children}</DashboardProfileContext.Provider>;
}

export function useDashboardProfile() {
  const context = React.useContext(DashboardProfileContext);
  if (!context) {
    throw new Error('useDashboardProfile must be used within DashboardProfileProvider');
  }
  return context;
}
