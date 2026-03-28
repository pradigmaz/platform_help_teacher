'use client';

import * as React from 'react';
import { AdminAPI, type AdminProfile } from '@/lib/api/admin';

export type AdminSessionUser = AdminProfile & {
  onboarding_completed: boolean;
  role: 'admin' | 'teacher' | 'student';
};

interface AdminSessionContextValue {
  user: AdminSessionUser | null;
  isLoading: boolean;
  refetch: () => Promise<AdminSessionUser | null>;
}

const AdminSessionContext = React.createContext<AdminSessionContextValue | null>(null);

async function loadAdminSession(): Promise<AdminSessionUser | null> {
  try {
    return await AdminAPI.getProfile();
  } catch {
    return null;
  }
}

export function AdminSessionProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<AdminSessionUser | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  const refetch = React.useCallback(async () => {
    const nextUser = await loadAdminSession();
    setUser(nextUser);
    return nextUser;
  }, []);

  React.useEffect(() => {
    let cancelled = false;

    const bootstrap = async () => {
      const nextUser = await loadAdminSession();
      if (!cancelled) {
        setUser(nextUser);
        setIsLoading(false);
      }
    };

    void bootstrap();

    return () => {
      cancelled = true;
    };
  }, []);

  const value = React.useMemo(
    () => ({
      user,
      isLoading,
      refetch,
    }),
    [user, isLoading, refetch],
  );

  return <AdminSessionContext.Provider value={value}>{children}</AdminSessionContext.Provider>;
}

export function useAdminSession() {
  const context = React.useContext(AdminSessionContext);
  if (!context) {
    throw new Error('useAdminSession must be used within AdminSessionProvider');
  }
  return context;
}
