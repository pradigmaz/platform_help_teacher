'use client';
'use no memo';

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { PublicReportAPI, PublicReportData, ApiError } from '@/lib/api';
import { toast } from '@/components/ui/sonner';
import { PinDialog } from './components/PinDialog';
import { ReportHeader } from './components/ReportHeader';
import { ReportSummaryCards } from './components/ReportSummaryCards';
import { ReportStudentTable } from './components/ReportStudentTable';
import { AttendanceChart, AttendanceTrend } from './components/AttendanceChart';
import { LabProgressChart } from './components/LabProgressChart';
import { TodayLessonsCard } from './components/TodayLessonsCard';
import { LoadingSkeleton, ErrorDisplay } from './components/PageStates';
import { ReportToolbar } from './components/ReportToolbar';
import { SubjectSelectionCard } from './components/SubjectSelectionCard';
import {
  filterStudentsBySubgroup,
  getAvailableSubgroups,
  getAttendanceDistributionForSubgroup,
  getLabProgressForSubgroup,
  type ReportSubgroupFilter,
} from './components/reportFilters';
import {
  parseReportAttestation,
  parseReportSubjectId,
  type ReportAttestation,
  withReportNavigation,
} from './reportNavigation';

interface PublicReportClientProps {
  code: string;
  initialAttestationType?: ReportAttestation;
}

type PageState =
  | { status: 'loading' }
  | { status: 'pin_required' }
  | { status: 'loaded'; data: PublicReportData }
  | { status: 'error'; error: string; errorType: 'not_found' | 'expired' | 'deactivated' | 'generic' };

export function PublicReportClient({
  code,
  initialAttestationType = 'first',
}: PublicReportClientProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [state, setState] = useState<PageState>({ status: 'loading' });
  const [isReloading, setIsReloading] = useState(false);
  const [attestationType, setAttestationType] = useState<ReportAttestation>(initialAttestationType);
  const [selectedSubjectId, setSelectedSubjectId] = useState(() => parseReportSubjectId(searchParams.get('subject_id')) ?? '');
  const [selectedSubgroup, setSelectedSubgroup] = useState<ReportSubgroupFilter>('all');
  const requestIdRef = useRef(0);
  const loadedDataRef = useRef<PublicReportData | null>(null);

  const loadReport = useCallback(async (
    attType: ReportAttestation,
    subjectId: string,
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
      const data = await PublicReportAPI.getReport(code, attType, subjectId || undefined, options.signal);
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
          setState({ status: 'error', error: 'Отчёт не найден', errorType: 'not_found' });
        } else if (err.status === 410) {
          const isExpired = err.message.toLowerCase().includes('expired');
          setState({ status: 'error', error: isExpired ? 'Срок действия отчёта истёк' : 'Отчёт недоступен', errorType: isExpired ? 'expired' : 'deactivated' });
        } else {
          setState({ status: 'error', error: err.message, errorType: 'generic' });
        }
      } else {
        if (preserveData && loadedDataRef.current) {
          toast.error('Ошибка загрузки отчёта');
          return;
        }
        setState({ status: 'error', error: 'Ошибка загрузки отчёта', errorType: 'generic' });
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
    void loadReport(attestationType, selectedSubjectId, { preserveData, signal: controller.signal });
    return () => controller.abort();
  }, [attestationType, loadReport, selectedSubjectId]);

  useEffect(() => {
    const currentAttestation = parseReportAttestation(searchParams.get('attestation'));
    const currentSubjectId = parseReportSubjectId(searchParams.get('subject_id')) ?? '';
    if (currentAttestation === attestationType && currentSubjectId === selectedSubjectId) {
      return;
    }

    const nextParams = withReportNavigation(
      new URLSearchParams(searchParams.toString()),
      attestationType,
      selectedSubjectId || null,
    );
    const nextQuery = nextParams.toString();
    const nextUrl = nextQuery ? `${pathname}?${nextQuery}` : pathname;

    router.replace(nextUrl, { scroll: false });
  }, [attestationType, pathname, router, searchParams, selectedSubjectId]);

  useEffect(() => {
    const currentData = loadedDataRef.current;
    if (!currentData) {
      return;
    }

    const availableSubjectIds = new Set((currentData.available_subjects ?? []).map((subject) => subject.id));
    const normalizedSubjectId =
      currentData.selected_subject_id ??
      (availableSubjectIds.has(selectedSubjectId) ? selectedSubjectId : '');
    if (normalizedSubjectId !== selectedSubjectId) {
      setSelectedSubjectId(normalizedSubjectId);
    }

    const availableSubgroups = getAvailableSubgroups(currentData);
    if (!availableSubgroups.includes(selectedSubgroup)) {
      setSelectedSubgroup('all');
    }
  }, [selectedSubgroup, selectedSubjectId, state]);

  const handleAttestationChange = (value: string) => {
    const newType = value as ReportAttestation;
    setAttestationType(newType);
  };

  const handlePinSuccess = () => {
    void loadReport(attestationType, selectedSubjectId);
  };

  const data = state.status === 'loaded' ? state.data : null;
  const subgroupOptions = useMemo(
    (): ReportSubgroupFilter[] => data ? getAvailableSubgroups(data) : ['all'],
    [data],
  );
  const filteredStudents = useMemo(
    () => data ? filterStudentsBySubgroup(data.students, selectedSubgroup) : [],
    [data, selectedSubgroup],
  );
  const attendanceDistribution = useMemo(
    () => data
      ? getAttendanceDistributionForSubgroup(data.attendance_distribution, data.attendance_stats, selectedSubgroup)
      : { present: 0, late: 0, excused: 0, absent: 0 },
    [data, selectedSubgroup],
  );
  const labProgress = useMemo(
    () => data ? getLabProgressForSubgroup(data.lab_progress, data.lab_progress_by_subgroup, selectedSubgroup) : [],
    [data, selectedSubgroup],
  );

  if (state.status === 'loading') {
    return <LoadingSkeleton />;
  }
  if (state.status === 'pin_required') {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <PinDialog code={code} open={true} onSuccess={handlePinSuccess} />
      </div>
    );
  }
  if (state.status === 'error') {
    return <ErrorDisplay error={state.error} errorType={state.errorType} />;
  }
  if (!data) {
    return <LoadingSkeleton />;
  }

  const isSecondAvailable = data.is_second_available ?? false;
  const requiresSubject = Boolean(data.requires_subject);
  const subjectSelectionPending = requiresSubject && !data.selected_subject_id;

  return (
    <div className="space-y-6">
      <ReportHeader data={data} />

      <ReportToolbar
        attestationType={attestationType}
        onAttestationChange={handleAttestationChange}
        isSecondAvailable={isSecondAvailable}
        selectedSubjectId={selectedSubjectId}
        onSubjectChange={setSelectedSubjectId}
        availableSubjects={data.available_subjects ?? []}
        selectedSubgroup={selectedSubgroup}
        onSubgroupChange={setSelectedSubgroup}
        subgroupOptions={subgroupOptions}
        isReloading={isReloading}
        requiresSubject={requiresSubject}
      />

      {subjectSelectionPending ? (
        <SubjectSelectionCard
          title="Выберите предмет для аттестации"
          description="В этой аттестации у группы несколько предметов. Сначала выберите предмет, потом отчёт покажет баллы, посещаемость и список студентов."
          subjects={data.available_subjects ?? []}
          value={selectedSubjectId}
          onChange={setSelectedSubjectId}
        />
      ) : (
        <>
          <ReportSummaryCards data={data} students={filteredStudents} selectedSubgroup={selectedSubgroup} />

          {(data.show_attendance || data.show_grades) && (
            <div className="space-y-6">
              <div className="grid gap-6 md:grid-cols-3">
                {data.show_attendance && (
                  <AttendanceChart
                    distribution={attendanceDistribution}
                    stats={data.attendance_stats}
                    selectedSubgroup={selectedSubgroup}
                  />
                )}
                {data.show_grades && (
                  <div className="md:col-span-2">
                    <LabProgressChart
                      progress={labProgress}
                      selectedSubgroup={selectedSubgroup}
                    />
                  </div>
                )}
              </div>
              {data.show_attendance && <AttendanceTrend stats={data.attendance_stats} selectedSubgroup={selectedSubgroup} />}
            </div>
          )}

          {(data.today_lessons?.length || data.lesson_history?.length) && <TodayLessonsCard todayLessons={data.today_lessons} lessonHistory={data.lesson_history} showNames={data.show_names} />}
          <ReportStudentTable data={data} students={filteredStudents} code={code} attestationType={attestationType} />
        </>
      )}
    </div>
  );
}
