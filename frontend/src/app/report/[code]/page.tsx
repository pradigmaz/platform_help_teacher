'use client';
'use no memo';

import { useState, useEffect, use } from 'react';
import { PublicReportAPI, PublicReportData, ApiError } from '@/lib/api';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent } from '@/components/ui/card';
import { AlertCircle, FileX, Clock } from 'lucide-react';
import { PinDialog } from './components/PinDialog';
import { ReportHeader } from './components/ReportHeader';
import { ReportSummaryCards } from './components/ReportSummaryCards';
import { ReportStudentTable } from './components/ReportStudentTable';
import { AttendanceChart } from './components/AttendanceChart';
import { LabProgressChart } from './components/LabProgressChart';

interface PageProps {
  params: Promise<{ code: string }>;
}

type PageState = 
  | { status: 'loading' }
  | { status: 'pin_required' }
  | { status: 'loaded'; data: PublicReportData }
  | { status: 'error'; error: string; errorType: 'not_found' | 'expired' | 'deactivated' | 'generic' };

export default function PublicReportPage({ params }: PageProps) {
  const { code } = use(params);
  const [state, setState] = useState<PageState>({ status: 'loading' });
  const [pinVerified, setPinVerified] = useState(false);

  const loadReport = async () => {
    setState({ status: 'loading' });
    try {
      const data = await PublicReportAPI.getReport(code);
      setState({ status: 'loaded', data });
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          // PIN required
          setState({ status: 'pin_required' });
        } else if (err.status === 404) {
          setState({ 
            status: 'error', 
            error: 'Отчёт не найден', 
            errorType: 'not_found' 
          });
        } else if (err.status === 410) {
          // Gone - expired or deactivated
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
        setState({ 
          status: 'error', 
          error: 'Ошибка загрузки отчёта', 
          errorType: 'generic' 
        });
      }
    }
  };

  useEffect(() => {
    loadReport();
  }, [code, pinVerified]);

  const handlePinSuccess = () => {
    setPinVerified(true);
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

  return (
    <div className="space-y-6">
      <ReportHeader data={data} />
      <ReportSummaryCards data={data} />
      
      {/* Charts section */}
      {(data.attendance_distribution || data.lab_progress) && (
        <div className="grid gap-6 md:grid-cols-2">
          {data.attendance_distribution && data.show_attendance && (
            <AttendanceChart distribution={data.attendance_distribution} />
          )}
          {data.lab_progress && data.lab_progress.length > 0 && data.show_grades && (
            <LabProgressChart progress={data.lab_progress} />
          )}
        </div>
      )}
      
      <ReportStudentTable data={data} code={code} />
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div className="space-y-4">
        <div className="flex justify-between">
          <div className="space-y-2">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-48" />
          </div>
          <div className="flex gap-2">
            <Skeleton className="h-9 w-20" />
            <Skeleton className="h-9 w-20" />
          </div>
        </div>
        <div className="flex gap-4">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-4 w-32" />
        </div>
      </div>

      {/* Summary cards skeleton */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map(i => (
          <Skeleton key={i} className="h-28 rounded-xl" />
        ))}
      </div>

      {/* Table skeleton */}
      <Skeleton className="h-96 rounded-xl" />
    </div>
  );
}

interface ErrorDisplayProps {
  error: string;
  errorType: 'not_found' | 'expired' | 'deactivated' | 'generic';
}

function ErrorDisplay({ error, errorType }: ErrorDisplayProps) {
  const icons = {
    not_found: <FileX className="h-12 w-12 text-muted-foreground" />,
    expired: <Clock className="h-12 w-12 text-amber-500" />,
    deactivated: <AlertCircle className="h-12 w-12 text-red-500" />,
    generic: <AlertCircle className="h-12 w-12 text-red-500" />,
  };

  const descriptions = {
    not_found: 'Проверьте правильность ссылки или обратитесь к преподавателю',
    expired: 'Срок действия ссылки истёк. Обратитесь к преподавателю за новой ссылкой',
    deactivated: 'Преподаватель деактивировал этот отчёт',
    generic: 'Попробуйте обновить страницу или обратитесь к преподавателю',
  };

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <Card className="max-w-md w-full">
        <CardContent className="pt-6 text-center space-y-4">
          <div className="flex justify-center">
            {icons[errorType]}
          </div>
          <div className="space-y-2">
            <h2 className="text-xl font-semibold">{error}</h2>
            <p className="text-sm text-muted-foreground">
              {descriptions[errorType]}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
