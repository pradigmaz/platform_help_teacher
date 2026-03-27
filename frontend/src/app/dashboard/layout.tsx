'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { AceternitySidebarLayout } from '@/components/dashboard/AceternitySidebar';
import { ImpersonationBanner } from '@/components/dashboard/ImpersonationBanner';
import { FeedbackFab } from '@/components/feedback/FeedbackFab';
import { Skeleton } from '@/components/ui/skeleton';
import { DashboardProfileProvider, useDashboardProfile } from './DashboardProfileProvider';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <DashboardProfileProvider>
      <DashboardLayoutShell>{children}</DashboardLayoutShell>
    </DashboardProfileProvider>
  );
}

function DashboardLayoutShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { profile, isLoading, error } = useDashboardProfile();

  useEffect(() => {
    if (!error) {
      return;
    }

    toast.error('Ошибка авторизации');
    router.push('/');
  }, [error, router]);

  if (isLoading || !profile) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <Skeleton className="h-12 w-48" />
      </div>
    );
  }

  return (
    <>
      <ImpersonationBanner />
      <AceternitySidebarLayout
        user={{
          name: profile.full_name || 'Студент',
          username: profile.username,
          group: profile.group?.code,
        }}
      >
        {children}
      </AceternitySidebarLayout>
      <FeedbackFab />
    </>
  );
}
