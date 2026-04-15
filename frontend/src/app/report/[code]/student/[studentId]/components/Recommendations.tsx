'use client';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle, ArrowUpRight, CheckCircle2, Lightbulb } from 'lucide-react';
import { cn } from '@/lib/utils';

interface RecommendationsProps {
  recommendations: string[];
  isPassing?: boolean;
  isEarlySemester?: boolean;
}

export function Recommendations({ recommendations, isPassing, isEarlySemester }: RecommendationsProps) {
  if (recommendations.length === 0 || isEarlySemester) {
    return null;
  }

  const isAtRisk = !isPassing;

  return (
    <Card
      className={cn(
        'group relative overflow-hidden border-border/60 bg-card/95 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/25 hover:bg-accent/10 hover:shadow-lg focus-within:border-primary/25 focus-within:shadow-lg',
        isAtRisk && 'border-amber-500/20 bg-amber-500/5',
      )}
    >
      <div
        className={cn(
          'pointer-events-none absolute inset-x-6 top-0 h-px bg-gradient-to-r from-transparent to-transparent',
          isAtRisk ? 'via-amber-500/35' : 'via-blue-500/35',
        )}
      />
      <div
        className={cn(
          'pointer-events-none absolute -right-10 -top-10 h-28 w-28 rounded-full opacity-0 blur-3xl transition-opacity duration-200 group-hover:opacity-100 group-focus-within:opacity-100',
          isAtRisk ? 'bg-amber-500/15' : 'bg-blue-500/15',
        )}
      />
      <CardHeader className="space-y-4 border-b border-border/60 bg-muted/20 pb-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              {isAtRisk ? (
                <AlertTriangle className="h-5 w-5 text-amber-500" />
              ) : (
                <Lightbulb className="h-5 w-5 text-blue-500" />
              )}
              <CardTitle className="text-lg">
                {isAtRisk ? 'Что сделать в первую очередь' : 'Как удержать результат'}
              </CardTitle>
            </div>
            <p className="text-sm text-muted-foreground">
              Короткие действия, которые помогут улучшить или закрепить текущий результат.
            </p>
          </div>
          <Badge
            variant="outline"
            className={cn(
              'rounded-full border px-3 py-1 text-xs font-medium',
              isAtRisk
                ? 'border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-300'
                : 'border-blue-500/20 bg-blue-500/10 text-blue-700 dark:text-blue-300',
            )}
          >
            {isAtRisk ? 'Приоритет: высокий' : 'Режим удержания'}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4 p-6">
        <div className="space-y-3">
          {recommendations.map((recommendation, index) => (
            <div
              key={`${recommendation}-${index}`}
              className="flex items-start gap-3 rounded-2xl border border-border/60 bg-background/80 px-4 py-3"
            >
              <div
                className={cn(
                  'mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold',
                  isAtRisk
                    ? 'bg-amber-500/10 text-amber-700 dark:text-amber-300'
                    : 'bg-blue-500/10 text-blue-700 dark:text-blue-300',
                )}
              >
                {index + 1}
              </div>
              <div className="min-w-0 flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <ArrowUpRight className="h-4 w-4 text-muted-foreground" />
                  <p className="text-sm font-medium text-foreground">Действие {index + 1}</p>
                </div>
                <p className="text-sm leading-relaxed text-muted-foreground">{recommendation}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="flex items-start gap-2 rounded-2xl border border-border/60 bg-muted/20 px-4 py-3 text-sm text-muted-foreground">
          <CheckCircle2 className="mt-0.5 h-4 w-4 text-green-500" />
          <p>
            {isAtRisk
              ? 'Если начать с первых пунктов, шанс быстро закрыть отставание выше.'
              : 'Регулярное выполнение этих шагов поможет не потерять текущий результат.'}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
