'use client';

import * as React from 'react';
import { AdminAPI, type AdminProfile } from '@/lib/api/admin';
import api from '@/lib/api';

export type AdminSessionUser = AdminProfile & {
  onboarding_completed: boolean;
  role: 'admin' | 'teacher' | 'student';
};

interface AdminSessionContextValue {
  user: AdminSessionUser | null;
  feedbackCount: number;
  isLoading: boolean;
  refetch: () => Promise<AdminSessionUser | null>;
  refetchFeedbackCount: () => Promise<number>;
}

const AdminSessionContext = React.createContext<AdminSessionContextValue | null>(null);

let inFlightAdminSessionRequest: Promise<AdminSessionUser | null> | null = null;
let inFlightFeedbackCountRequest: Promise<number> | null = null;

async function loadAdminSession(): Promise<AdminSessionUser | null> {
  if (!inFlightAdminSessionRequest) {
    inFlightAdminSessionRequest = AdminAPI.getProfile()
      .catch(() => null)
      .finally(() => {
        inFlightAdminSessionRequest = null;
      });
  }

  return inFlightAdminSessionRequest;
}

async function loadFeedbackCount(): Promise<number> {
  if (!inFlightFeedbackCountRequest) {
    inFlightFeedbackCountRequest = api
      .get<{ count: number }>('/feedback/count/new')
      .then(({ data }) => data.count)
      .catch(() => 0)
      .finally(() => {
        inFlightFeedbackCountRequest = null;
      });
  }

  return inFlightFeedbackCountRequest;
}

export function AdminSessionProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<AdminSessionUser | null>(null);
  const [feedbackCount, setFeedbackCount] = React.useState(0);
  const [isLoading, setIsLoading] = React.useState(true);

  const refetch = React.useCallback(async () => {
    const nextUser = await loadAdminSession();
    setUser(nextUser);
    return nextUser;
  }, []);

  const refetchFeedbackCount = React.useCallback(async () => {
    const nextCount = await loadFeedbackCount();
    setFeedbackCount(nextCount);
    return nextCount;
  }, []);

  React.useEffect(() => {
    let cancelled = false;

    const bootstrap = async () => {
      const [nextUser, nextFeedbackCount] = await Promise.all([loadAdminSession(), loadFeedbackCount()]);
      if (cancelled) {
        return;
      }

      setUser(nextUser);
      setFeedbackCount(nextFeedbackCount);
      setIsLoading(false);
    };

    void bootstrap();

    return () => {
      cancelled = true;
    };
  }, []);

  React.useEffect(() => {
    const intervalId = window.setInterval(() => {
      void refetchFeedbackCount();
    }, 60_000);

    return () => window.clearInterval(intervalId);
  }, [refetchFeedbackCount]);

  const value = React.useMemo(
    () => ({
      user,
      feedbackCount,
      isLoading,
      refetch,
      refetchFeedbackCount,
    }),
    [user, feedbackCount, isLoading, refetch, refetchFeedbackCount],
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
