'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { StudentAPI, StudentProfile } from '@/lib/api';
import { AceternitySidebarLayout } from '@/components/dashboard/AceternitySidebar';
import { Skeleton } from '@/components/ui/skeleton';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const data = await StudentAPI.getProfile();
        setProfile(data);
      } catch {
        toast.error('Ошибка авторизации');
        router.push('/');
      } finally {
        setLoading(false);
      }
    };
    loadProfile();
  }, [router]);

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <Skeleton className="h-12 w-48" />
      </div>
    );
  }

  return (
    <AceternitySidebarLayout
      user={{
        name: profile?.full_name || 'Студент',
        username: profile?.username,
        group: profile?.group?.code,
      }}
    >
      {children}
    </AceternitySidebarLayout>
  );
}
