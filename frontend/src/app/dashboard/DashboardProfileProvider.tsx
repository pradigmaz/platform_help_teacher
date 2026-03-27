'use client';

import * as React from 'react';
import { StudentAPI, type StudentProfile } from '@/lib/api';

interface DashboardProfileContextValue {
  profile: StudentProfile | null;
  isLoading: boolean;
  error: unknown;
}

const DashboardProfileContext = React.createContext<DashboardProfileContextValue | null>(null);

let inFlightProfileRequest: Promise<StudentProfile> | null = null;

async function loadDashboardProfile() {
  if (!inFlightProfileRequest) {
    inFlightProfileRequest = StudentAPI.getProfile().finally(() => {
      inFlightProfileRequest = null;
    });
  }

  return inFlightProfileRequest;
}

export function DashboardProfileProvider({ children }: { children: React.ReactNode }) {
  const [profile, setProfile] = React.useState<StudentProfile | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<unknown>(null);

  React.useEffect(() => {
    let cancelled = false;

    const bootstrap = async () => {
      try {
        const nextProfile = await loadDashboardProfile();
        if (!cancelled) {
          setProfile(nextProfile);
          setError(null);
        }
      } catch (nextError) {
        if (!cancelled) {
          setProfile(null);
          setError(nextError);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void bootstrap();

    return () => {
      cancelled = true;
    };
  }, []);

  const value = React.useMemo(
    () => ({
      profile,
      isLoading,
      error,
    }),
    [profile, isLoading, error],
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
