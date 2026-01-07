'use client';

import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import {
  StudentAPI,
  StudentProfile,
  StudentAttendance,
  StudentLab,
  StudentAttestation,
} from '@/lib/api';
import { Effect } from '@/components/animate-ui/primitives/effects/effect';
import { Skeleton } from '@/components/ui/skeleton';
import { StatusHero, QuickStats, DeadlinesList } from '@/components/dashboard';

export default function DashboardOverview() {
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [attendance, setAttendance] = useState<StudentAttendance | null>(null);
  const [labs, setLabs] = useState<StudentLab[]>([]);
  const [attestation, setAttestation] = useState<StudentAttestation | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [profileData, attendanceData, labsData, att1, att2] = await Promise.all([
          StudentAPI.getProfile(),
          StudentAPI.getAttendance(),
          StudentAPI.getLabs(),
          StudentAPI.getAttestation('first'),
          StudentAPI.getAttestation('second'),
        ]);
        setProfile(profileData);
        setAttendance(attendanceData);
        setLabs(labsData);
        // Use current attestation (first if available, else second)
        setAttestation(att1?.error ? att2 : att1);
      } catch {
        toast.error('Ошибка загрузки данных');
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  if (loading) return <DashboardSkeleton />;

  const firstName = profile?.full_name?.split(' ')[1] || 'Студент';
  const groupCode = profile?.group?.code;

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <Effect fade slide={{ direction: 'down', offset: 10 }} inView inViewOnce>
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-foreground">
            Привет, {firstName}!
          </h1>
          <p className="text-sm text-muted-foreground">
            {groupCode ? `Группа ${groupCode}` : 'Краткий обзор успеваемости'}
          </p>
        </div>
      </Effect>

      {/* Status Hero - Attestation */}
      <StatusHero attestation={attestation} />

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <QuickStats labs={labs} attendance={attendance} />
      </div>

      {/* Deadlines List */}
      <DeadlinesList labs={labs} maxItems={5} />
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      <div className="space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-32" />
      </div>
      <Skeleton className="h-40 rounded-xl" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Skeleton className="h-32 rounded-xl" />
        <Skeleton className="h-32 rounded-xl" />
        <Skeleton className="h-32 rounded-xl" />
      </div>
      <Skeleton className="h-48 rounded-xl" />
    </div>
  );
}
