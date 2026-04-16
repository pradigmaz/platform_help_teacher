'use client';

import { AlertCircle, ArrowLeft, Clock, FileX } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

export function LoadingSkeleton({ onBack }: { onBack: () => void }) {
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
        {[1, 2, 3, 4].map((index) => (
          <Skeleton key={index} className="h-28 rounded-xl" />
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

export function ErrorDisplay({ error, errorType, onBack }: ErrorDisplayProps) {
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
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4">
      <Card className="w-full max-w-md">
        <CardContent className="space-y-4 pt-6 text-center">
          <div className="flex justify-center">{icons[errorType]}</div>
          <div className="space-y-2">
            <h2 className="text-xl font-semibold">{error}</h2>
            <p className="text-sm text-muted-foreground">{descriptions[errorType]}</p>
          </div>
          <Button variant="outline" onClick={onBack}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Вернуться к отчёту
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
