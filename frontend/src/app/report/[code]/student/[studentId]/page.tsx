'use client';

import { useState, useEffect, use } from 'react';
import { useRouter } from 'next/navigation';
import { PublicReportAPI, StudentDetailData, ApiError } from '@/lib/api';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle, FileX, Clock, ArrowLeft } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { BlurFade } from '@/components/ui/blur-fade';
import { ScoreBreakdown } from './components/ScoreBreakdown';
import { ComparisonChart } from './components/ComparisonChart';
import { AttendanceHistory } from './components/AttendanceHistory';
import { LabSubmissions } from './components/LabSubmissions';
import { Recommendations } from './components/Recommendations';

// Format group code: ИС1231ОТ -> ИС1-231-ОТ
function formatGroupCode(code: string): string {
  const match = code.match(/^([А-ЯA-Z]{2,3})(\d)(\d{3})([А-ЯA-Z]{2})$/i);
  if (match) {
    return `${match[1]}${match[2]}-${match[3]}-${match[4]}`;
  }
  return code;
}

interface PageProps {
  params: Promise<{ code: string; studentId: string }>;
}

type PageState = 
  | { status: 'loading' }
  | { status: 'loaded'; data: StudentDetailData }
  | { status: 'error'; error: string; errorType: 'not_found' | 'expired' | 'deactivated' | 'generic' };

export default function StudentDetailPage({ params }: PageProps) {
  const { code, studentId } = use(params);
  const router = useRouter();
  const [state, setState] = useState<PageState>({ status: 'loading' });

  useEffect(() => {
    const loadStudent = async () => {
      setState({ status: 'loading' });
      try {
        const data = await PublicReportAPI.getStudent(code, studentId);
        setState({ status: 'loaded', data });
      } catch (err) {
        if (err instanceof ApiError) {
          if (err.status === 404) {
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
    loadStudent();
  }, [code, studentId]);

  const handleBack = () => {
    router.push(`/report/${code}`);
  };

  if (state.status === 'loading') {
    return <LoadingSkeleton onBack={handleBack} />;
  }

  if (state.status === 'error') {
    return <ErrorDisplay error={state.error} errorType={state.errorType} onBack={handleBack} />;
  }

  const { data } = state;

  return (
    <div className="space-y-6">
      {/* Header with rank */}
      <BlurFade delay={0.1} inView>
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={handleBack}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">
                {data.name || `Студент ${studentId.slice(0, 8)}`}
              </h1>
              {data.rank_in_group && data.total_in_group && (
                <Badge variant="secondary" className="text-sm">
                  #{data.rank_in_group} из {data.total_in_group}
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground">
              Группа {formatGroupCode(data.group_code)}
            </p>
          </div>
        </div>
      </BlurFade>

      {/* Score Breakdown */}
      <BlurFade delay={0.15} inView>
        <ScoreBreakdown data={data} />
      </BlurFade>

      {/* Comparison Chart */}
      {data.group_average_score !== undefined && (
        <BlurFade delay={0.2} inView>
          <ComparisonChart data={data} />
        </BlurFade>
      )}

      {/* Recommendations for failing students */}
      {data.recommendations && data.recommendations.length > 0 && (
        <BlurFade delay={0.25} inView>
          <Recommendations recommendations={data.recommendations} isPassing={data.is_passing} />
        </BlurFade>
      )}

      {/* Attendance History */}
      {data.attendance_history && data.attendance_history.length > 0 && (
        <BlurFade delay={0.3} inView>
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

      {/* Lab Submissions */}
      {data.lab_submissions && data.lab_submissions.length > 0 && (
        <BlurFade delay={0.35} inView>
          <LabSubmissions 
            submissions={data.lab_submissions}
            completed={data.labs_completed || 0}
            total={data.labs_total || 0}
          />
        </BlurFade>
      )}
    </div>
  );
}


function LoadingSkeleton({ onBack }: { onBack: () => void }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={onBack}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        {[1, 2, 3, 4].map(i => (
          <Skeleton key={i} className="h-28 rounded-xl" />
        ))}
      </div>
      <Skeleton className="h-64 rounded-xl" />
      <Skeleton className="h-48 rounded-xl" />
    </div>
  );
}

interface ErrorDisplayProps {
  error: string;
  errorType: 'not_found' | 'expired' | 'deactivated' | 'generic';
  onBack: () => void;
}

function ErrorDisplay({ error, errorType, onBack }: ErrorDisplayProps) {
  const icons = {
    not_found: <FileX className="h-12 w-12 text-muted-foreground" />,
    expired: <Clock className="h-12 w-12 text-amber-500" />,
    deactivated: <AlertCircle className="h-12 w-12 text-red-500" />,
    generic: <AlertCircle className="h-12 w-12 text-red-500" />,
  };

  const descriptions = {
    not_found: 'Студент не найден в этом отчёте',
    expired: 'Срок действия ссылки истёк',
    deactivated: 'Отчёт был деактивирован',
    generic: 'Попробуйте обновить страницу',
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
      <Card className="max-w-md w-full">
        <CardContent className="pt-6 text-center space-y-4">
          <div className="flex justify-center">{icons[errorType]}</div>
          <div className="space-y-2">
            <h2 className="text-xl font-semibold">{error}</h2>
            <p className="text-sm text-muted-foreground">{descriptions[errorType]}</p>
          </div>
          <Button variant="outline" onClick={onBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Вернуться к отчёту
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
