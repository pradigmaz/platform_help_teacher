'use client';
'use no memo';

import { useState, useEffect, useCallback, useRef } from 'react';
import { PublicReportAPI, PublicReportData, ApiError } from '@/lib/api';
import { toast } from '@/components/ui/sonner';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PinDialog } from './components/PinDialog';
import { ReportHeader } from './components/ReportHeader';
import { ReportSummaryCards } from './components/ReportSummaryCards';
import { ReportStudentTable } from './components/ReportStudentTable';
import { AttendanceChart, AttendanceTrend } from './components/AttendanceChart';
import { LabProgressChart } from './components/LabProgressChart';
import { TodayLessonsCard } from './components/TodayLessonsCard';
import { LoadingSkeleton, ErrorDisplay } from './components/PageStates';

interface PublicReportClientProps {
  code: string;
}

type AttestationType = 'first' | 'second';

type PageState = 
  | { status: 'loading' }
  | { status: 'pin_required' }
  | { status: 'loaded'; data: PublicReportData }
  | { status: 'error'; error: string; errorType: 'not_found' | 'expired' | 'deactivated' | 'generic' };

export function PublicReportClient({ code }: PublicReportClientProps) {
  const [state, setState] = useState<PageState>({ status: 'loading' });
  const [isReloading, setIsReloading] = useState(false);
  const [attestationType, setAttestationType] = useState<AttestationType>('first');
  const requestIdRef = useRef(0);
  const loadedDataRef = useRef<PublicReportData | null>(null);

  const loadReport = useCallback(async (
    attType: AttestationType,
    options: { preserveData?: boolean; signal?: AbortSignal } = {},
  ) => {
    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;
    const preserveData = options.preserveData ?? false;

    if (preserveData && loadedDataRef.current) {
      setIsReloading(true);
    } else {
      setState({ status: 'loading' });
    }

    try {
      const data = await PublicReportAPI.getReport(code, attType, options.signal);
      if (requestId !== requestIdRef.current || options.signal?.aborted) {
        return;
      }
      loadedDataRef.current = data;
      setState({ status: 'loaded', data });
    } catch (err) {
      if (requestId !== requestIdRef.current || options.signal?.aborted) {
        return;
      }

      if (err instanceof ApiError) {
        if (err.status === 401) {
          setState({ status: 'pin_required' });
          return;
        }

        if (preserveData && loadedDataRef.current) {
          toast.error(err.message || 'Ошибка загрузки отчёта');
          return;
        }

        if (err.status === 404) {
          setState({ 
            status: 'error', 
            error: 'Отчёт не найден', 
            errorType: 'not_found' 
          });
        } else if (err.status === 410) {
          const isExpired = err.message.toLowerCase().includes('expired');
          setState({ 
            status: 'error', 
            error: isExpired ? 'Срок действия отчёта истёк' : 'Отчёт недоступен',
            errorType: isExpired ? 'expired' : 'deactivated'
          });
        } else {
          setState({ 
            status: 'error', 
            error: err.message, 
            errorType: 'generic' 
          });
        }
      } else {
        if (preserveData && loadedDataRef.current) {
          toast.error('Ошибка загрузки отчёта');
          return;
        }
        setState({ 
          status: 'error', 
          error: 'Ошибка загрузки отчёта', 
          errorType: 'generic' 
        });
      }
    } finally {
      if (requestId === requestIdRef.current) {
        setIsReloading(false);
      }
    }
  }, [code]);

  useEffect(() => {
    const controller = new AbortController();
    const preserveData = loadedDataRef.current !== null;
    void loadReport(attestationType, { preserveData, signal: controller.signal });
    return () => controller.abort();
  }, [attestationType, loadReport]);

  const handleAttestationChange = (value: string) => {
    const newType = value as AttestationType;
    setAttestationType(newType);
  };

  const handlePinSuccess = () => {
    void loadReport(attestationType);
  };

  // Loading state
  if (state.status === 'loading') {
    return <LoadingSkeleton />;
  }

  // PIN required
  if (state.status === 'pin_required') {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <PinDialog 
          code={code} 
          open={true} 
          onSuccess={handlePinSuccess} 
        />
      </div>
    );
  }

  // Error state
  if (state.status === 'error') {
    return <ErrorDisplay error={state.error} errorType={state.errorType} />;
  }

  // Loaded state
  const { data } = state;
  const isSecondAvailable = data.is_second_available ?? false;

  return (
    <div className="space-y-6">
      <ReportHeader data={data} />
      
      {/* Attestation Tabs */}
      <Tabs value={attestationType} onValueChange={handleAttestationChange}>
        <TabsList>
          <TabsTrigger value="first">1 аттестация</TabsTrigger>
          <TabsTrigger value="second" disabled={!isSecondAvailable}>
            2 аттестация
          </TabsTrigger>
        </TabsList>
      </Tabs>
      {isReloading && (
        <p className="text-sm text-muted-foreground">Обновляем данные для выбранной аттестации...</p>
      )}
      <p className="text-sm text-muted-foreground">
        Показатели посещаемости считаются для выбранной аттестации, а история занятий показывает отдельный процент по каждому занятию.
      </p>
      
      <ReportSummaryCards data={data} />
      
      {/* Charts section - 2 сверху (1+2 колонки), 1 снизу */}
      {(data.show_attendance || data.show_grades) && (
        <div className="space-y-6">
          <div className="grid gap-6 md:grid-cols-3">
            {data.show_attendance && (
              <AttendanceChart 
                distribution={data.attendance_distribution || { present: 0, late: 0, excused: 0, absent: 0 }} 
                stats={data.attendance_stats}
                hasSubgroups={data.has_subgroups}
              />
            )}
            {data.show_grades && (
              <div className="md:col-span-2">
                <LabProgressChart 
                  progress={data.lab_progress || []} 
                  progressBySubgroup={data.lab_progress_by_subgroup}
                  hasSubgroups={data.has_subgroups} 
                />
              </div>
            )}
          </div>
          {data.show_attendance && (
            <AttendanceTrend stats={data.attendance_stats} hasSubgroups={data.has_subgroups} />
          )}
        </div>
      )}
      
      {/* Today's lessons and history */}
      {(data.today_lessons?.length || data.lesson_history?.length) && (
        <TodayLessonsCard 
          todayLessons={data.today_lessons} 
          lessonHistory={data.lesson_history}
          showNames={data.show_names} 
        />
      )}
      
      <ReportStudentTable data={data} code={code} />
    </div>
  );
}
