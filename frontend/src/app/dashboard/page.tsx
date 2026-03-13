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
import { getCurrentAttestationType } from '@/lib/attestation-period';
import { formatGroupCode } from '@/lib/utils';
import { useSemesterInfo } from '@/hooks/useSemesterInfo';
import { Effect } from '@/components/animate-ui/primitives/effects/effect';
import { Skeleton } from '@/components/ui/skeleton';
import { StatusHero, QuickStats, DeadlinesList } from '@/components/dashboard';

export default function DashboardOverview() {
  const semesterInfo = useSemesterInfo();
  const {
    loading: semesterInfoLoading,
    academicYear,
    semester,
    semesterStartDate,
  } = semesterInfo;
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [attendance, setAttendance] = useState<StudentAttendance | null>(null);
  const [labs, setLabs] = useState<StudentLab[]>([]);
  const [attestation, setAttestation] = useState<StudentAttestation | null>(null);

  useEffect(() => {
    if (semesterInfoLoading) {
      return;
    }

    const loadData = async () => {
      try {
        const [profileData, attendanceData, labsData] = await Promise.all([
          StudentAPI.getProfile(),
          StudentAPI.getAttendance(),
          StudentAPI.getLabs(),
        ]);
        setProfile(profileData);
        setAttendance(attendanceData);
        setLabs(labsData);
        const preferredType = getCurrentAttestationType({
          academicYear,
          semester,
          semesterStartDate,
        });

        const labSubjectIds = [
          ...new Set(
            labsData
              .map((lab) => lab.subject_id)
              .filter((subjectId): subjectId is string => typeof subjectId === 'string' && subjectId.length > 0)
          ),
        ];
        let resolvedSubjectId = labSubjectIds.length === 1 ? labSubjectIds[0] : undefined;

        if (!resolvedSubjectId) {
          const attestationSubjects = await StudentAPI.getAttestationSubjects(preferredType);
          if (attestationSubjects.length === 1) {
            resolvedSubjectId = attestationSubjects[0].id;
          } else if (attestationSubjects.length > 1) {
            setAttestation({
              attestation_type: preferredType,
              subject_id: null,
              total_score: 0,
              grade: '-',
              is_passing: false,
              error: 'Для расчёта аттестации нужно выбрать предмет',
            });
            return;
          }
        }

        const [att1, att2] = await Promise.all([
          StudentAPI.getAttestation('first', resolvedSubjectId),
          StudentAPI.getAttestation('second', resolvedSubjectId),
        ]);
        const preferred = preferredType === 'first' ? att1 : att2;
        const fallback = preferredType === 'first' ? att2 : att1;
        setAttestation(preferred?.error ? fallback : preferred);
      } catch {
        toast.error('Ошибка загрузки данных');
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [semesterInfoLoading, academicYear, semester, semesterStartDate]);

  if (loading) return <DashboardSkeleton />;

  const firstName = profile?.full_name?.split(' ')[1] || 'Студент';
  const groupCode = profile?.group?.code;

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <Effect fade slide={{ direction: 'down', offset: 10 }} inView inViewOnce>
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-foreground">
            Привет, {firstName}! 👋
          </h1>
          <p className="text-sm text-muted-foreground">
            {groupCode ? `Группа ${formatGroupCode(groupCode)} • Твой прогресс` : 'Краткий обзор успеваемости'}
          </p>
        </div>
      </Effect>

      {/* Status Hero - Attestation */}
      <StatusHero attestation={attestation} />

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <QuickStats labs={labs} attendance={attendance} attestation={attestation} />
      </div>

      {/* Deadlines List */}
      <DeadlinesList labs={labs} maxItems={5} />
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
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
