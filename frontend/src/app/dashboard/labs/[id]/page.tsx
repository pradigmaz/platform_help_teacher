'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { StudentAPI, StudentLabDetail } from '@/lib/api';
import { CardSpotlight } from '@/components/ui/card-spotlight';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { IconArrowLeft, IconCheck, IconClock, IconX, IconCalendar, IconTarget, IconBook, IconCode, IconQuestionMark, IconPlayerPlay, IconHandStop } from '@tabler/icons-react';
import { motion } from 'motion/react';
import { cn } from '@/lib/utils';
import Link from 'next/link';

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
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/dashboard/labs">
          <Button variant="ghost" size="icon"><IconArrowLeft className="h-5 w-5" /></Button>
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="outline">№{lab.number}</Badge>
            <Badge className={cn(status.bg, status.color)}>{status.label}</Badge>
          </div>
          <h1 className="text-2xl font-bold text-foreground">{lab.title}</h1>
          {lab.topic && <p className="text-muted-foreground">{lab.topic}</p>}
        </div>
      </div>

      {/* Status & Actions */}
      <CardSpotlight className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className={cn("p-3 rounded-xl", status.bg)}>
              <StatusIcon className={cn("h-8 w-8", status.color)} />
            </div>
            <div>
              <p className="text-lg font-semibold text-foreground">{status.label}</p>
              {lab.submission?.grade !== undefined && (
                <p className="text-2xl font-bold text-foreground">{lab.submission.grade}/{lab.max_grade}</p>
              )}
              {lab.deadline && (
                <p className="text-sm text-muted-foreground flex items-center gap-1">
                  <IconCalendar className="h-4 w-4" />
                  Дедлайн: {new Date(lab.deadline).toLocaleDateString('ru-RU')}
                </p>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            {!lab.submission && (
              <Button onClick={handleMarkReady} disabled={actionLoading}>
                {actionLoading ? '...' : <><IconPlayerPlay className="h-4 w-4 mr-2" />Готов сдать</>}
              </Button>
            )}
            {lab.submission?.status === 'READY' && (
              <Button variant="destructive" onClick={handleCancelReady} disabled={actionLoading}>
                {actionLoading ? '...' : <><IconHandStop className="h-4 w-4 mr-2" />Выйти из очереди</>}
              </Button>
            )}
            {lab.submission?.status === 'REJECTED' && (
              <Button onClick={handleMarkReady} disabled={actionLoading}>
                {actionLoading ? '...' : 'Пересдать'}
              </Button>
            )}
          </div>
        </div>
        {lab.submission?.feedback && (
          <div className="mt-4 p-4 rounded-lg bg-neutral-50 dark:bg-neutral-900 border">
            <p className="text-sm font-medium text-foreground mb-1">Комментарий преподавателя:</p>
            <p className="text-sm text-muted-foreground">{lab.submission.feedback}</p>
          </div>
        )}
      </CardSpotlight>

      {/* Variant */}
      {lab.variant_number && (
        <CardSpotlight className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <IconCode className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold text-foreground">Ваш вариант: {lab.variant_number}</h2>
          </div>
          {lab.variant_data && (
            <div className="space-y-2">
              {lab.variant_data.description && (
                <p className="text-foreground">{lab.variant_data.description}</p>
              )}
              {lab.variant_data.test_data && (
                <div className="p-3 rounded-lg bg-neutral-100 dark:bg-neutral-900 font-mono text-sm">
                  {lab.variant_data.test_data}
                </div>
              )}
            </div>
          )}
        </CardSpotlight>
      )}

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
            <IconBook className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold text-foreground">Что записать в тетрадь</h2>
          </div>
          <p className="text-muted-foreground whitespace-pre-line">{lab.formatting_guide}</p>
        </CardSpotlight>
      )}

      {/* Questions */}
      {lab.questions && lab.questions.length > 0 && (
        <CardSpotlight className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <IconQuestionMark className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold text-foreground">Контрольные вопросы</h2>
          </div>
          <ol className="list-decimal list-inside space-y-2">
            {lab.questions.map((q, i) => (
              <li key={i} className="text-muted-foreground">{q}</li>
            ))}
          </ol>
        </CardSpotlight>
      )}
    </div>
  );
}

function LabDetailSkeleton() {
  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
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
