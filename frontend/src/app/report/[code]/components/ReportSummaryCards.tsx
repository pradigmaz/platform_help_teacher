'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { ArrowDown, ArrowUp, AlertTriangle, PartyPopper, HelpCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { PublicReportData } from '@/lib/api';
import { BlurFade } from '@/components/ui/blur-fade';
import { getStudentWord } from '@/lib/utils/pluralize';

interface ReportSummaryCardsProps {
  data: PublicReportData;
}

export function ReportSummaryCards({ data }: ReportSummaryCardsProps) {
  const showGrades = data.show_grades;
  
  const scores = data.students
    .map(s => s.total_score)
    .filter((s): s is number => s !== undefined);
  
  const minScore = scores.length > 0 ? Math.min(...scores) : 0;
  const maxScore = scores.length > 0 ? Math.max(...scores) : 0;

  const maxPoints = data.max_points ?? 35;
  const minPassingPoints = data.min_passing_points ?? 20;

  const hasAtRiskStudents = (data.failing_students ?? 0) > 0;
  const showPassFail = data.attestation_type === 'second' && !data.is_early_semester;

  if (!showGrades || scores.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      {/* Risk Banner - только для 2-й аттестации */}
      {showPassFail && (
        <BlurFade delay={0.1} inView>
          <RiskBanner 
            hasRisk={hasAtRiskStudents} 
            failingCount={data.failing_students ?? 0}
            totalCount={data.total_students}
          />
        </BlurFade>
      )}

      {/* Score Card with distribution */}
      <BlurFade delay={0.2} inView>
        <Card>
          <CardContent className="p-4">
            {/* Score Range */}
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              {/* Min */}
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-red-500/10">
                  <ArrowDown className="h-4 w-4 text-red-500" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Минимум</p>
                  <p className="text-lg font-semibold">{minScore.toFixed(1)}</p>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="flex-1 space-y-2">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>0</span>
                  <span className="font-medium text-foreground">
                    Средний: {data.average_score?.toFixed(1) || '—'}
                  </span>
                  <span>{maxPoints}</span>
                </div>
                <div className="relative h-3 bg-secondary rounded-full overflow-hidden">
                  <div 
                    className="absolute top-0 bottom-0 w-0.5 bg-yellow-500 z-10"
                    style={{ left: `${(minPassingPoints / maxPoints) * 100}%` }}
                  />
                  <Progress 
                    value={((data.average_score || 0) / maxPoints) * 100} 
                    className="h-full"
                  />
                </div>
                <div className="flex items-center justify-center gap-1 text-xs text-muted-foreground">
                  <span>Порог зачёта: {minPassingPoints} б.</span>
                  {data.grade_scale && (
                    <GradeScalePopover 
                      gradeScale={data.grade_scale} 
                      attestationType={data.attestation_type}
                      maxPoints={maxPoints}
                    />
                  )}
                </div>
              </div>

              {/* Max */}
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-green-500/10">
                  <ArrowUp className="h-4 w-4 text-green-500" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Максимум</p>
                  <p className="text-lg font-semibold">{maxScore.toFixed(1)}</p>
                </div>
              </div>
            </div>

            {/* Grade Distribution */}
            {data.grade_distribution && Object.keys(data.grade_distribution).length > 0 && !data.is_early_semester && (
              <div className="mt-4 pt-4 border-t">
                <GradeDistribution distribution={data.grade_distribution} />
              </div>
            )}
          </CardContent>
        </Card>
      </BlurFade>
    </div>
  );
}

function GradeDistribution({ distribution }: { distribution: Record<string, number> }) {
  const gradeConfig = [
    { key: 'неуд', label: '2', color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
    { key: 'уд', label: '3', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' },
    { key: 'хор', label: '4', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
    { key: 'отл', label: '5', color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' },
  ];

  return (
    <div className="flex gap-2">
      {gradeConfig.map(({ key, label, color }) => {
        const count = distribution[key] ?? 0;
        return (
          <div 
            key={key}
            className={cn("flex-1 text-center py-2 rounded-lg", color)}
          >
            <div className="text-xl font-bold">{count}</div>
            <div className="text-xs opacity-80">на {label}</div>
          </div>
        );
      })}
    </div>
  );
}

interface GradeScalePopoverProps {
  gradeScale: Record<string, number[]>;
  attestationType?: string;
  maxPoints: number;
}

function GradeScalePopover({ gradeScale, attestationType = 'first', maxPoints }: GradeScalePopoverProps) {
  const gradeConfig = [
    { key: 'неуд', label: '2', color: 'text-red-600 dark:text-red-400' },
    { key: 'уд', label: '3', color: 'text-yellow-600 dark:text-yellow-400' },
    { key: 'хор', label: '4', color: 'text-blue-600 dark:text-blue-400' },
    { key: 'отл', label: '5', color: 'text-green-600 dark:text-green-400' },
  ];

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button className="inline-flex items-center hover:text-foreground transition-colors">
          <HelpCircle className="h-3.5 w-3.5" />
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-64 p-3" align="center">
        <p className="text-sm font-medium mb-2">
          Шкала оценок ({attestationType === 'first' ? '1-я атт.' : '2-я атт.'})
        </p>
        <div className="space-y-1.5">
          {gradeConfig.map(({ key, label, color }) => {
            const range = gradeScale[key];
            if (!range) return null;
            return (
              <div key={key} className="flex justify-between text-sm">
                <span className={cn("font-medium", color)}>Оценка {label}</span>
                <span className="text-muted-foreground">{range[0]}–{range[1]} б.</span>
              </div>
            );
          })}
        </div>
        <p className="text-xs text-muted-foreground mt-2 pt-2 border-t">
          Максимум: {maxPoints} баллов
        </p>
      </PopoverContent>
    </Popover>
  );
}

interface RiskBannerProps {
  hasRisk: boolean;
  failingCount: number;
  totalCount: number;
}

function RiskBanner({ hasRisk, failingCount, totalCount }: RiskBannerProps) {
  if (hasRisk) {
    return (
      <div className="flex items-center gap-3 p-4 rounded-lg bg-red-500/10 border border-red-500/20">
        <div className="p-2 rounded-full bg-red-500/20 animate-pulse">
          <AlertTriangle className="h-5 w-5 text-red-500" />
        </div>
        <div className="flex-1">
          <p className="font-medium text-red-600 dark:text-red-400">
            Требуется внимание
          </p>
          <p className="text-sm text-red-600/80 dark:text-red-400/80">
            {failingCount} из {totalCount} {getStudentWord(totalCount)} не получают зачёт
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 p-4 rounded-lg bg-green-500/10 border border-green-500/20">
      <div className="p-2 rounded-full bg-green-500/20">
        <PartyPopper className="h-5 w-5 text-green-500" />
      </div>
      <div className="flex-1">
        <p className="font-medium text-green-600 dark:text-green-400">
          Отличная работа!
        </p>
        <p className="text-sm text-green-600/80 dark:text-green-400/80">
          Все студенты успешно справляются
        </p>
      </div>
    </div>
  );
}
