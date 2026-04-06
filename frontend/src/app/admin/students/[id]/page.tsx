'use client';

import { useParams, useRouter } from 'next/navigation';
import { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';
import { BlurFade } from '@/components/ui/blur-fade';
import dynamic from 'next/dynamic';
import api from '@/lib/api';
import { runSingleFlight } from '@/lib/single-flight';
import { StudentActivitiesList } from '@/components/admin/StudentActivitiesList';
import { StudentAuditHistory } from '@/components/admin/StudentAuditHistory';
import {
  LabSubmission,
  StudentProfile,
  StudentProfileCard,
  StudentStatsCards,
  StudentProgressCard,
  StudentLabsList,
  COLORS,
} from './components';

const StudentLabsChart = dynamic(() => import('@/components/admin/StudentLabsChart'), {
  ssr: false,
  loading: () => <Skeleton className="h-[350px] w-full" />,
});

export default function StudentProfilePage() {
  const params = useParams();
  const router = useRouter();
  const studentId = params.id as string;
  
  const [student, setStudent] = useState<StudentProfile | null>(null);
  const [labs, setLabs] = useState<LabSubmission[]>([]);
  const [labsLoading, setLabsLoading] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resettingTelegram, setResettingTelegram] = useState(false);
  const [resettingVk, setResettingVk] = useState(false);
  const requestIdRef = useRef(0);

  const fetchStudentProfile = useCallback(async (requestId = requestIdRef.current) => {
    const data = await runSingleFlight(`admin-student-profile:${studentId}`, async () => {
      const response = await api.get<StudentProfile>(`/admin/students/${studentId}`, {
        params: { include_labs: false },
      });
      return response.data;
    });
    if (requestIdRef.current === requestId) {
      setStudent(data);
      setError(null);
    }
    return data;
  }, [studentId]);

  const fetchStudentLabs = useCallback(
    async ({ requestId = requestIdRef.current, silent = false }: { requestId?: number; silent?: boolean } = {}) => {
      if (requestIdRef.current === requestId) {
        setLabsLoading(true);
      }

      try {
        const data = await runSingleFlight(`admin-student-labs:${studentId}`, async () => {
          const response = await api.get<LabSubmission[]>(`/admin/students/${studentId}/labs`);
          return response.data;
        });
        if (requestIdRef.current === requestId) {
          setLabs(data);
        }
        return data;
      } catch (error) {
        if (requestIdRef.current === requestId) {
          setLabs([]);
          if (!silent) {
            toast.error('Не удалось загрузить лабораторные работы');
          }
        }
        throw error;
      } finally {
        if (requestIdRef.current === requestId) {
          setLabsLoading(false);
        }
      }
    },
    [studentId],
  );

  const handleResetTelegram = async () => {
    try {
      setResettingTelegram(true);
      await api.post(`/admin/students/${studentId}/reset-telegram`);
      toast.success('Telegram отвязан');
      await fetchStudentProfile();
    } catch {
      toast.error('Ошибка при сбросе Telegram');
    } finally {
      setResettingTelegram(false);
    }
  };

  const handleResetVk = async () => {
    try {
      setResettingVk(true);
      await api.post(`/admin/students/${studentId}/reset-social?platform=vk`);
      toast.success('VK отвязан');
      await fetchStudentProfile();
    } catch {
      toast.error('Ошибка при сбросе VK');
    } finally {
      setResettingVk(false);
    }
  };

  const refreshStudent = async () => {
    const requestId = ++requestIdRef.current;
    await fetchStudentProfile(requestId);
    await fetchStudentLabs({ requestId, silent: true }).catch(() => {
      toast.error('Не удалось обновить лабораторные работы');
    });
  };

  useEffect(() => {
    const requestId = ++requestIdRef.current;

    setLoading(true);
    setError(null);
    setStudent(null);
    setLabs([]);
    setLabsLoading(true);

    const loadStudent = async () => {
      try {
        await fetchStudentProfile(requestId);
      } catch {
        if (requestIdRef.current === requestId) {
          setStudent(null);
          setLabs([]);
          setError('Не удалось загрузить данные студента');
          setLabsLoading(false);
        }
        return;
      } finally {
        if (requestIdRef.current === requestId) {
          setLoading(false);
        }
      }
    };

    const loadLabs = async () => {
      await fetchStudentLabs({ requestId, silent: true });
    };

    void (async () => {
      await loadStudent();
      if (requestIdRef.current !== requestId) {
        return;
      }
      await loadLabs().catch(() => undefined);
    })();

    return () => {
      if (requestIdRef.current === requestId) {
        requestIdRef.current += 1;
      }
    };
  }, [fetchStudentLabs, fetchStudentProfile]);

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto p-8 space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-32 w-full" />
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-32" />)}
        </div>
      </div>
    );
  }

  if (error || !student) {
    return (
      <div className="max-w-6xl mx-auto p-8">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="w-4 h-4 mr-2" /> Назад
        </Button>
        <p className="text-center text-red-500 mt-8">{error || 'Студент не найден'}</p>
      </div>
    );
  }

  const { stats } = student;
  const notSubmitted = stats.labs_total - stats.labs_submitted;

  const labsStatusData = [
    { name: 'Принято', value: stats.labs_accepted, color: COLORS.accepted },
    { name: 'На проверке', value: stats.labs_pending, color: COLORS.pending },
    { name: 'Отклонено', value: stats.labs_rejected, color: COLORS.rejected },
    { name: 'Не сдано', value: notSubmitted - stats.labs_overdue, color: COLORS.notSubmitted },
    { name: 'Долги', value: stats.labs_overdue, color: COLORS.overdue },
  ];

  return (
    <div className="max-w-6xl mx-auto p-8 space-y-6">
      <BlurFade delay={0.1}>
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <h1 className="text-2xl font-bold">Профиль студента</h1>
        </div>
      </BlurFade>

      <BlurFade delay={0.2}>
        <StudentProfileCard
          student={student}
          onResetTelegram={handleResetTelegram}
          resettingTelegram={resettingTelegram}
          onResetVk={handleResetVk}
          resettingVk={resettingVk}
          onTransferSuccess={refreshStudent}
        />
      </BlurFade>

      <StudentStatsCards stats={stats} />

      <BlurFade delay={0.48}>
        <StudentActivitiesList studentId={student.id} studentName={student.full_name} />
      </BlurFade>

      <div className="grid md:grid-cols-2 gap-6">
        <BlurFade delay={0.5}>
          <StudentLabsChart data={labsStatusData} />
        </BlurFade>
        <BlurFade delay={0.55}>
          <StudentProgressCard stats={stats} />
        </BlurFade>
      </div>

      <BlurFade delay={0.55}>
        <StudentAuditHistory userId={studentId} />
      </BlurFade>

      <BlurFade delay={0.6}>
        <StudentLabsList labs={labs} isLoading={labsLoading} />
      </BlurFade>
    </div>
  );
}
