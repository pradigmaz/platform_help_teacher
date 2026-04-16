'use client';

import { useState, useEffect, use, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { PublicReportAPI, StudentDetailData, ApiError } from '@/lib/api';
import { cn } from '@/lib/utils';
import { BlurFade } from '@/components/ui/blur-fade';
import { PinDialog } from '../../components/PinDialog';
import { HeroCard } from './components/HeroCard';
import { ScoreBreakdown } from './components/ScoreBreakdown';
import { ComparisonChart } from './components/ComparisonChart';
import { AttendanceHistory } from './components/AttendanceHistory';
import { LabSubmissions } from './components/LabSubmissions';
import { Recommendations } from './components/Recommendations';
import { SubjectSelectionCard } from '../../components/SubjectSelectionCard';
import { ErrorDisplay, LoadingSkeleton } from './components/PageStateViews';
import { StudentReportHeader } from './components/StudentReportHeader';
import { AttestationComparisonCards } from './components/AttestationComparisonCards';
import {
  buildReportHref,
  buildStudentReportHref,
  parseReportAttestation,
  parseReportSubjectId,
} from '../../reportNavigation';

interface PageProps {
  params: Promise<{ code: string; studentId: string }>;
}

type PageState = 
  | { status: 'loading' }
  | { status: 'pin_required' }
  | { status: 'loaded'; data: StudentDetailData; firstAttestationData?: StudentDetailData | null }
  | { status: 'error'; error: string; errorType: 'not_found' | 'expired' | 'deactivated' | 'generic' };

export default function StudentDetailPage({ params }: PageProps) {
  const { code, studentId } = use(params);
  return <StudentDetailPageContent code={code} studentId={studentId} />;
}

interface StudentDetailPageContentProps {
  code: string;
  studentId: string;
}

export function StudentDetailPageContent({
  code,
  studentId,
}: StudentDetailPageContentProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [state, setState] = useState<PageState>({ status: 'loading' });
  const [reloadToken, setReloadToken] = useState(0);
  const requestIdRef = useRef(0);
  const attestationType = parseReportAttestation(searchParams.get('attestation'));
  const subjectId = parseReportSubjectId(searchParams.get('subject_id'));

  useEffect(() => {
    const controller = new AbortController();
    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;

    const loadStudent = async () => {
      setState({ status: 'loading' });

      try {
        const data = await PublicReportAPI.getStudent(
          code,
          studentId,
          attestationType,
          subjectId ?? undefined,
          controller.signal,
        );

        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        const shouldLoadFirstAttestation =
          attestationType === 'second' && !(data.requires_subject && !data.selected_subject_id);
        let firstAttestationData: StudentDetailData | null = null;

        if (shouldLoadFirstAttestation) {
          try {
            firstAttestationData = await PublicReportAPI.getStudent(
              code,
              studentId,
              'first',
              data.selected_subject_id ?? subjectId ?? undefined,
              controller.signal,
            );

            if (requestId !== requestIdRef.current || controller.signal.aborted) {
              return;
            }
          } catch {
            if (requestId !== requestIdRef.current || controller.signal.aborted) {
              return;
            }
            firstAttestationData = null;
          }
        }

        setState({ status: 'loaded', data, firstAttestationData });
      } catch (err) {
        if (requestId !== requestIdRef.current || controller.signal.aborted) {
          return;
        }

        if (err instanceof ApiError) {
          if (err.status === 401) {
            setState({ status: 'pin_required' });
          } else if (err.status === 404) {
            setState({ status: 'error', error: 'Студент не найден', errorType: 'not_found' });
          } else if (err.status === 410) {
            const isExpired = err.message.toLowerCase().includes('expired');
            setState({ 
              status: 'error', 
              error: isExpired ? 'Срок действия отчёта истёк' : 'Отчёт недоступен',
              errorType: isExpired ? 'expired' : 'deactivated'
            });
          } else {
            setState({ status: 'error', error: err.message, errorType: 'generic' });
          }
        } else {
          setState({ status: 'error', error: 'Ошибка загрузки данных', errorType: 'generic' });
        }
      }
    };

    void loadStudent();
    return () => controller.abort();
  }, [attestationType, code, reloadToken, studentId, subjectId]);

  const handleBack = () => {
    router.push(buildReportHref(code, attestationType, subjectId));
  };

  const handlePinSuccess = () => {
    setState({ status: 'loading' });
    setReloadToken((current) => current + 1);
  };

  if (state.status === 'loading') {
    return <LoadingSkeleton onBack={handleBack} />;
  }

  if (state.status === 'pin_required') {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <PinDialog code={code} open={true} onSuccess={handlePinSuccess} />
      </div>
    );
  }

  if (state.status === 'error') {
    return <ErrorDisplay error={state.error} errorType={state.errorType} onBack={handleBack} />;
  }

  const { data, firstAttestationData } = state;
  const subjectSelectionPending = Boolean(data.requires_subject && !data.selected_subject_id);
  const hasRecommendations = Boolean(data.recommendations && data.recommendations.length > 0);
  const hasComparison = data.group_average_score !== undefined;

  if (subjectSelectionPending) {
    return (
      <div className="space-y-6">
        <SubjectSelectionCard
          title="Выберите предмет для аттестации"
          description="У этой группы в выбранной аттестации несколько предметов. Выберите предмет, чтобы открыть детальную карточку студента."
          subjects={data.available_subjects ?? []}
          value={subjectId ?? ''}
          onChange={(nextSubjectId) =>
            router.push(buildStudentReportHref(code, studentId, attestationType, nextSubjectId))
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <BlurFade delay={0.06} inView>
        <StudentReportHeader
          data={data}
          attestationType={attestationType}
          onBack={handleBack}
        />
      </BlurFade>

      {attestationType === 'second' && firstAttestationData && (
        <BlurFade delay={0.08} inView>
          <AttestationComparisonCards
            firstAttestationData={firstAttestationData}
            currentAttestationData={data}
          />
        </BlurFade>
      )}

      <BlurFade delay={0.1} inView>
        <HeroCard
          data={data}
          attestationType={attestationType}
        />
      </BlurFade>

      <BlurFade delay={0.15} inView>
        <ScoreBreakdown data={data} />
      </BlurFade>

      {(hasComparison || hasRecommendations) && (
        <div
          className={cn(
            'grid gap-6',
            hasComparison && hasRecommendations ? 'xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]' : undefined,
          )}
        >
          {hasComparison && (
            <BlurFade delay={0.2} inView>
              <ComparisonChart data={data} />
            </BlurFade>
          )}
          {hasRecommendations && data.recommendations && (
            <BlurFade delay={0.25} inView>
              <Recommendations
                recommendations={data.recommendations}
                isPassing={data.is_passing}
                isEarlySemester={data.is_early_semester}
              />
            </BlurFade>
          )}
        </div>
      )}

      {data.attendance_history && data.attendance_history.length > 0 && (
        <BlurFade delay={0.28} inView>
          <AttendanceHistory
            history={data.attendance_history}
            stats={{
              present: data.present_count || 0,
              late: data.late_count || 0,
              excused: data.excused_count || 0,
              absent: data.absent_count || 0,
              total: data.total_lessons || 0,
              rate: data.attendance_rate || 0,
            }}
          />
        </BlurFade>
      )}

      {data.lab_submissions && data.lab_submissions.length > 0 && (
        <BlurFade delay={0.32} inView>
          <LabSubmissions
            submissions={data.lab_submissions}
            completed={data.labs_completed || 0}
            total={data.labs_total || 0}
            isEarlySemester={data.is_early_semester}
          />
        </BlurFade>
      )}
    </div>
  );
}
