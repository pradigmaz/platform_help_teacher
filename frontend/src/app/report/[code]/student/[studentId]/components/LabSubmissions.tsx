'use client';

import { useMemo, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Progress } from '@/components/ui/progress';
import { LabSubmissionPublic } from '@/lib/api';
import { cn } from '@/lib/utils';
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  FlaskConical,
  XCircle,
} from 'lucide-react';

interface LabSubmissionsProps {
  submissions: LabSubmissionPublic[];
  completed: number;
  total: number;
  isEarlySemester?: boolean;
}

export function LabSubmissions({ submissions, completed, total, isEarlySemester }: LabSubmissionsProps) {
  const [expanded, setExpanded] = useState(false);
  const completionRate = total > 0 ? Math.round((completed / total) * 100) : 0;
  const orderedSubmissions = useMemo(
    () =>
      [...submissions].sort((left, right) => {
        const severityDelta = getStatusWeight(left, isEarlySemester) - getStatusWeight(right, isEarlySemester);
        if (severityDelta !== 0) {
          return severityDelta;
        }
        return left.lab_number - right.lab_number;
      }),
    [isEarlySemester, submissions],
  );

  const attentionSubmissions = orderedSubmissions.filter((lab) => getStatusWeight(lab, isEarlySemester) < 2);
  const stableSubmissions = orderedSubmissions.filter((lab) => getStatusWeight(lab, isEarlySemester) >= 2);
  const previewStableSubmissions = expanded ? stableSubmissions : stableSubmissions.slice(0, 4);

  return (
    <Card className="group relative overflow-hidden border-border/60 bg-card/95 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/25 hover:bg-accent/10 hover:shadow-lg focus-within:border-primary/25 focus-within:shadow-lg">
      <div className="pointer-events-none absolute inset-x-6 top-0 h-px bg-gradient-to-r from-transparent via-blue-500/35 to-transparent" />
      <div className="pointer-events-none absolute -right-10 -top-10 h-28 w-28 rounded-full bg-blue-500/15 opacity-0 blur-3xl transition-opacity duration-200 group-hover:opacity-100 group-focus-within:opacity-100" />
      <CardHeader className="space-y-4 border-b border-border/60 bg-muted/20 pb-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <FlaskConical className="h-5 w-5 text-muted-foreground" />
              <CardTitle className="text-lg">Лабораторные работы</CardTitle>
            </div>
            <p className="text-sm text-muted-foreground">
              Сначала показаны работы, которые требуют внимания.
            </p>
          </div>
          <Badge variant="outline" className={cn('rounded-full border px-3 py-1 text-sm font-medium', getCompletionTone(completionRate))}>
            {completed} из {total} · {completionRate}%
          </Badge>
        </div>

        <div className="space-y-2">
          <Progress value={completionRate} className={cn('h-2.5 rounded-full', getCompletionProgressClass(completionRate))} />
          <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
            <span>Требуют внимания: {attentionSubmissions.length}</span>
            <span>•</span>
            <span>Уже в порядке: {stableSubmissions.length}</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-5 p-6">
        {attentionSubmissions.length > 0 && (
          <div className="space-y-3">
            <div className="space-y-1">
              <p className="text-sm font-medium text-foreground">Требуют внимания</p>
              <p className="text-sm text-muted-foreground">
                Здесь несданные работы и те, что были отправлены с опозданием.
              </p>
            </div>
            <div className="space-y-3">
              {attentionSubmissions.map((lab) => (
                <LabRow key={lab.lab_id} lab={lab} isEarlySemester={isEarlySemester} />
              ))}
            </div>
          </div>
        )}

        {stableSubmissions.length > 0 && (
          <div className="space-y-3">
            <div className="space-y-1">
              <p className="text-sm font-medium text-foreground">Уже в порядке</p>
              <p className="text-sm text-muted-foreground">
                Сданные работы, которые не выглядят проблемными в текущий момент.
              </p>
            </div>

            <div className="space-y-3">
              {previewStableSubmissions.map((lab) => (
                <LabRow key={lab.lab_id} lab={lab} isEarlySemester={isEarlySemester} />
              ))}
            </div>

            {stableSubmissions.length > 4 && (
              <Collapsible open={expanded} onOpenChange={setExpanded} className="rounded-2xl border border-border/60 bg-muted/10">
                <div className="flex items-center justify-between gap-3 px-4 py-3">
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {expanded ? 'Свернуть остальные лабораторные' : `Показать ещё ${stableSubmissions.length - 4} лабораторные`}
                    </p>
                    <p className="text-xs text-muted-foreground">Полный список уже закрытых работ</p>
                  </div>
                  <CollapsibleTrigger asChild>
                    <Button variant="ghost" size="sm">
                      {expanded ? (
                        <>
                          <ChevronUp className="mr-2 h-4 w-4" />
                          Свернуть
                        </>
                      ) : (
                        <>
                          <ChevronDown className="mr-2 h-4 w-4" />
                          Показать
                        </>
                      )}
                    </Button>
                  </CollapsibleTrigger>
                </div>
                <CollapsibleContent className="space-y-3 border-t border-border/60 px-4 pb-4 pt-3">
                  {stableSubmissions.slice(4).map((lab) => (
                    <LabRow key={`${lab.lab_id}-extra`} lab={lab} isEarlySemester={isEarlySemester} />
                  ))}
                </CollapsibleContent>
              </Collapsible>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function LabRow({ lab, isEarlySemester }: { lab: LabSubmissionPublic; isEarlySemester?: boolean }) {
  const status = getStatusConfig(lab, isEarlySemester);
  const Icon = status.icon;

  return (
    <div className={cn('flex items-start gap-3 rounded-2xl border px-4 py-3', status.wrapperClassName)}>
      <div className={cn('mt-0.5 flex h-10 w-10 items-center justify-center rounded-xl border', status.badgeClassName)}>
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-sm font-medium text-foreground">
            Лаб. {lab.lab_number} · {lab.lab_name}
          </p>
          <Badge variant="outline" className={cn('rounded-full border px-2 py-0.5 text-[11px]', status.badgeClassName)}>
            {status.label}
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          {lab.submitted_at ? `Дата сдачи: ${formatDate(lab.submitted_at)}` : 'Дата сдачи пока не зафиксирована'}
        </p>
      </div>
      <div className="shrink-0 text-right">
        {lab.grade !== undefined && lab.grade !== null ? (
          <>
            <p className="text-lg font-semibold text-foreground">{lab.grade}</p>
            <p className="text-xs text-muted-foreground">из {lab.max_grade}</p>
          </>
        ) : (
          <p className="text-sm font-medium text-muted-foreground">Без оценки</p>
        )}
      </div>
    </div>
  );
}

function getStatusWeight(lab: LabSubmissionPublic, isEarlySemester?: boolean) {
  if (!lab.is_submitted) {
    return isEarlySemester ? 1 : 0;
  }

  if (lab.is_late) {
    return 1;
  }

  return 2;
}

function getStatusConfig(lab: LabSubmissionPublic, isEarlySemester?: boolean) {
  if (!lab.is_submitted) {
    return isEarlySemester
      ? {
          icon: Clock,
          label: 'Ожидается',
          wrapperClassName: 'border-slate-500/20 bg-slate-500/5',
          badgeClassName: 'border-slate-500/20 bg-slate-500/10 text-slate-700 dark:text-slate-300',
        }
      : {
          icon: XCircle,
          label: 'Не сдано',
          wrapperClassName: 'border-red-500/20 bg-red-500/5',
          badgeClassName: 'border-red-500/20 bg-red-500/10 text-red-700 dark:text-red-300',
        };
  }

  if (lab.is_late) {
    return {
      icon: AlertTriangle,
      label: 'Сдано с опозданием',
      wrapperClassName: 'border-amber-500/20 bg-amber-500/5',
      badgeClassName: 'border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-300',
    };
  }

  return {
    icon: CheckCircle2,
    label: 'Сдано',
    wrapperClassName: 'border-emerald-500/20 bg-emerald-500/5',
    badgeClassName: 'border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
  };
}

function getCompletionTone(rate: number) {
  if (rate >= 80) return 'border-green-500/20 bg-green-500/10 text-green-700 dark:text-green-300';
  if (rate >= 50) return 'border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-300';
  return 'border-red-500/20 bg-red-500/10 text-red-700 dark:text-red-300';
}

function getCompletionProgressClass(rate: number) {
  if (rate >= 80) return '[&>div]:bg-green-500';
  if (rate >= 50) return '[&>div]:bg-amber-500';
  return '[&>div]:bg-red-500';
}

function formatDate(dateStr: string) {
  try {
    return new Date(dateStr).toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return dateStr;
  }
}
