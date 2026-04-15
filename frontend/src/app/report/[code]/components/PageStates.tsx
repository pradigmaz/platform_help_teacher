'use client';

import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle, FileX, Clock } from 'lucide-react';

export function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="rounded-3xl border border-border/60 p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-2">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-10 w-72" />
            <Skeleton className="h-5 w-80" />
          </div>
          <div className="flex gap-2">
            <Skeleton className="h-9 w-28 rounded-full" />
            <Skeleton className="h-9 w-32 rounded-full" />
          </div>
        </div>
        <div className="mt-5 grid gap-3 md:grid-cols-3">
          <Skeleton className="h-28 rounded-2xl" />
          <Skeleton className="h-28 rounded-2xl" />
          <Skeleton className="h-28 rounded-2xl" />
        </div>
      </div>

      <div className="grid gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-4">
        {[1, 2, 3, 4].map(i => (
          <Skeleton key={i} className="h-36 rounded-3xl" />
        ))}
      </div>

      <Skeleton className="h-96 rounded-3xl" />
    </div>
  );
}

interface ErrorDisplayProps {
  error: string;
  errorType: 'not_found' | 'expired' | 'deactivated' | 'generic';
}

export function ErrorDisplay({ error, errorType }: ErrorDisplayProps) {
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
      <Card className="w-full max-w-lg rounded-3xl border-border/60 shadow-sm">
        <CardContent className="space-y-5 p-8 text-center">
          <div className="flex justify-center">
            {icons[errorType]}
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl font-semibold tracking-tight">{error}</h2>
            <p className="text-sm text-muted-foreground sm:text-base">
              {descriptions[errorType]}
            </p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row sm:justify-center">
            <Button type="button" onClick={() => window.location.reload()}>
              Обновить страницу
            </Button>
            <Button type="button" variant="outline" onClick={() => window.history.back()}>
              Вернуться назад
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
