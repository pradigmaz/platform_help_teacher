'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { StudentAPI, StudentLabDetail } from '@/lib/api';
import { CardSpotlight } from '@/components/ui/card-spotlight';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { IconArrowLeft, IconCheck, IconClock, IconX, IconTarget, IconBook, IconCode, IconQuestionMark, IconPlayerPlay, IconHandStop, IconAlertCircle, IconNotebook, IconFlask } from '@tabler/icons-react';
import { cn } from '@/lib/utils';
import Link from 'next/link';
import { LectureViewer } from '@/components/lectures';
import { SerializedEditorState } from 'lexical';
import { getQuestionText } from '@/lib/utils/question-utils';

export default function LabDetailPage() {
  const params = useParams();
  const router = useRouter();
  const labId = params.id as string;
  
  const [loading, setLoading] = useState(true);
  const [lab, setLab] = useState<StudentLabDetail | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const loadLab = async () => {
    try {
      const data = await StudentAPI.getLabDetail(labId);
      setLab(data);
    } catch {
      toast.error('Ошибка загрузки лабораторной');
      router.push('/dashboard/labs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLab();
  }, [labId]);

  const handleMarkReady = async () => {
    if (!lab) return;
    setActionLoading(true);
    try {
      await StudentAPI.markLabReady(lab.id);
      toast.success('Вы в очереди! Подойдите к преподавателю с тетрадью.');
      await loadLab();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || 'Ошибка');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancelReady = async () => {
    if (!lab) return;
    setActionLoading(true);
    try {
      await StudentAPI.cancelLabReady(lab.id);
      toast.success('Вы вышли из очереди');
      await loadLab();
    } catch {
      toast.error('Ошибка');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <LabDetailSkeleton />;
  if (!lab) return null;

  const getStatusConfig = () => {
    const status = lab.submission?.status;
    switch (status) {
      case 'ACCEPTED': return { icon: IconCheck, color: 'text-green-500', bg: 'bg-green-500/10', label: 'Принято' };
      case 'READY': return { icon: IconClock, color: 'text-yellow-500', bg: 'bg-yellow-500/10', label: 'В очереди на сдачу' };
      case 'REJECTED': return { icon: IconX, color: 'text-red-500', bg: 'bg-red-500/10', label: 'Отклонено' };
      default: return { icon: IconCode, color: 'text-blue-500', bg: 'bg-blue-500/10', label: 'Не сдано' };
    }
  };

  const status = getStatusConfig();
  const StatusIcon = status.icon;

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/dashboard/labs">
          <Button variant="ghost" size="icon"><IconArrowLeft className="h-5 w-5" /></Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-foreground">
            Лабораторная работа №{lab.number}. {lab.title}
          </h1>
          {lab.topic && <p className="text-muted-foreground mt-1">{lab.topic}</p>}
        </div>
      </div>

      {/* Status */}
      <CardSpotlight className="p-6">
        <div className="flex items-center gap-4">
          <div className={cn("p-3 rounded-xl", status.bg)}>
            <StatusIcon className={cn("h-8 w-8", status.color)} />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <Badge className={cn(status.bg, status.color)}>{status.label}</Badge>
              {lab.submission?.grade !== undefined && (
                <span className="text-xl font-bold text-foreground">{lab.submission.grade}/{lab.max_grade}</span>
              )}
            </div>
          </div>
        </div>
        {lab.submission?.feedback && (
          <div className="mt-4 p-4 rounded-lg bg-neutral-50 dark:bg-neutral-900 border">
            <p className="text-sm font-medium text-foreground mb-1">Комментарий преподавателя:</p>
            <p className="text-sm text-muted-foreground">{lab.submission.feedback}</p>
          </div>
        )}
      </CardSpotlight>

      {/* Goal */}
      {lab.goal && (
        <CardSpotlight className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <IconTarget className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold text-foreground">Цель работы</h2>
          </div>
          <p className="text-muted-foreground">{lab.goal}</p>
        </CardSpotlight>
      )}

      {/* Formatting Guide */}
      {lab.formatting_guide && (
        <CardSpotlight className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <IconNotebook className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold text-foreground">Оформление в тетрадь</h2>
          </div>
          <p className="text-muted-foreground whitespace-pre-line">{lab.formatting_guide}</p>
        </CardSpotlight>
      )}

      {/* Theory */}
      {lab.theory_content && (
        <CardSpotlight className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <IconBook className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold text-foreground">Теоретическая часть</h2>
          </div>
          <LectureViewer content={lab.theory_content as unknown as SerializedEditorState} />
        </CardSpotlight>
      )}

      {/* Practice */}
      {lab.practice_content && (
        <CardSpotlight className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <IconFlask className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold text-foreground">Практическая часть</h2>
          </div>
          <LectureViewer content={lab.practice_content as unknown as SerializedEditorState} />
        </CardSpotlight>
      )}

      {/* Variant */}
      <CardSpotlight className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <IconCode className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold text-foreground">
            {lab.variant_number ? `Ваш вариант: ${lab.variant_number}` : 'Ваш вариант'}
          </h2>
        </div>
        {lab.variant_number && lab.variant_data ? (
          <div className="space-y-4">
            {/* Lexical content если есть */}
            {lab.variant_data.content ? (
              <LectureViewer content={lab.variant_data.content as unknown as SerializedEditorState} />
            ) : lab.variant_data.description ? (
              <p className="text-foreground">{lab.variant_data.description}</p>
            ) : null}
            {lab.variant_data.test_data && (
              <div className="p-3 rounded-lg bg-neutral-100 dark:bg-neutral-900 font-mono text-sm whitespace-pre-wrap">
                {lab.variant_data.test_data}
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center py-6 text-center">
            <IconAlertCircle className="h-10 w-10 text-rose-500 mb-3" />
            <p className="text-lg font-medium text-foreground">Вариант не назначен</p>
            <p className="text-muted-foreground">Обратитесь к преподавателю для назначения варианта.</p>
          </div>
        )}
      </CardSpotlight>

      {/* Questions */}
      {lab.questions && lab.questions.length > 0 && (
        <CardSpotlight className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <IconQuestionMark className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold text-foreground">Контрольные вопросы</h2>
          </div>
          <div className="space-y-4">
            {lab.questions.map((q, i) => {
              const questionObj = typeof q === 'string' ? { text: q } : q;
              return (
                <div key={i} className="flex gap-3 p-4 rounded-lg bg-muted/50">
                  <span className="flex items-center justify-center h-6 w-6 rounded-full bg-primary/10 text-primary text-sm font-medium shrink-0">
                    {i + 1}
                  </span>
                  <div className="flex-1">
                    {questionObj.content ? (
                      <LectureViewer content={questionObj.content as unknown as SerializedEditorState} />
                    ) : (
                      <p className="text-foreground">{questionObj.text || getQuestionText(q)}</p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </CardSpotlight>
      )}

      {/* Action Button */}
      <div className="flex justify-center pt-4">
        {(!lab.submission || lab.submission.status === 'NEW') && (
          <Button size="lg" onClick={handleMarkReady} disabled={actionLoading}>
            {actionLoading ? '...' : <><IconPlayerPlay className="h-5 w-5 mr-2" />Готов сдать</>}
          </Button>
        )}
        {lab.submission?.status === 'READY' && (
          <Button size="lg" variant="destructive" onClick={handleCancelReady} disabled={actionLoading}>
            {actionLoading ? '...' : <><IconHandStop className="h-5 w-5 mr-2" />Выйти из очереди</>}
          </Button>
        )}
        {lab.submission?.status === 'REJECTED' && (
          <Button size="lg" onClick={handleMarkReady} disabled={actionLoading}>
            {actionLoading ? '...' : <><IconPlayerPlay className="h-5 w-5 mr-2" />Исправил, сдать снова</>}
          </Button>
        )}
      </div>
    </div>
  );
}

function LabDetailSkeleton() {
  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center gap-4">
        <Skeleton className="h-10 w-10 rounded-lg" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-8 w-64" />
        </div>
      </div>
      <Skeleton className="h-32 rounded-xl" />
      <Skeleton className="h-24 rounded-xl" />
      <Skeleton className="h-24 rounded-xl" />
      <Skeleton className="h-48 rounded-xl" />
    </div>
  );
}
