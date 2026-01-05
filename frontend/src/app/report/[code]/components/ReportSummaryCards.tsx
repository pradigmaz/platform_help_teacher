'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Users, CheckCircle2, XCircle, TrendingUp, ArrowDown, ArrowUp, AlertTriangle, PartyPopper } from 'lucide-react';
import { cn } from '@/lib/utils';
import { PublicReportData } from '@/lib/api';
import { NumberTicker } from '@/components/ui/number-ticker';
import { BorderBeam } from '@/components/ui/border-beam';
import { BlurFade } from '@/components/ui/blur-fade';

interface ReportSummaryCardsProps {
  data: PublicReportData;
}

export function ReportSummaryCards({ data }: ReportSummaryCardsProps) {
  const showGrades = data.show_grades;
  
  // Calculate stats from students if not provided
  const scores = data.students
    .map(s => s.total_score)
    .filter((s): s is number => s !== undefined);
  
  const minScore = scores.length > 0 ? Math.min(...scores) : 0;
  const maxScore = scores.length > 0 ? Math.max(...scores) : 0;
  
  const passRate = data.total_students > 0 && data.passing_students !== undefined
    ? Math.round((data.passing_students / data.total_students) * 100)
    : 0;

  // Assume max points is 40 (standard attestation)
  const maxPoints = 40;
  const minPassingPoints = 18;

  const hasAtRiskStudents = (data.failing_students ?? 0) > 0;

  return (
    <div className="space-y-4">
      {/* Risk Banner */}
      {showGrades && (
        <BlurFade delay={0.1} inView>
          <RiskBanner 
            hasRisk={hasAtRiskStudents} 
            failingCount={data.failing_students ?? 0}
            totalCount={data.total_students}
          />
        </BlurFade>
      )}

      {/* Main Stats Cards */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        <BlurFade delay={0.15} inView>
          <StatCard
            icon={<Users className="h-5 w-5" />}
            label="Всего студентов"
            value={data.total_students}
            description="в группе"
            color="default"
            borderColor="border-l-slate-500"
          />
        </BlurFade>
        
        {showGrades && data.passing_students !== undefined && (
          <BlurFade delay={0.2} inView>
            <StatCard
              icon={<CheckCircle2 className="h-5 w-5" />}
              label="Зачёт"
              value={data.passing_students}
              description={`${passRate}%`}
              color="success"
              borderColor="border-l-green-500"
            />
          </BlurFade>
        )}
        
        {showGrades && data.failing_students !== undefined && (
          <BlurFade delay={0.25} inView>
            <StatCard
              icon={<XCircle className="h-5 w-5" />}
              label="Незачёт"
              value={data.failing_students}
              description={`${100 - passRate}%`}
              color="destructive"
              borderColor="border-l-red-500"
              highlight={hasAtRiskStudents}
            />
          </BlurFade>
        )}
        
        {showGrades && data.average_score !== undefined && (
          <BlurFade delay={0.3} inView>
            <StatCard
              icon={<TrendingUp className="h-5 w-5" />}
              label="Средний балл"
              value={data.average_score}
              description={`из ${maxPoints}`}
              color="primary"
              borderColor="border-l-blue-500"
              isDecimal
            />
          </BlurFade>
        )}
      </div>

      {/* Score Range Card (only if grades visible) */}
      {showGrades && scores.length > 0 && (
        <BlurFade delay={0.35} inView>
          <Card>
          <CardContent className="p-4">
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
                  {/* Passing threshold marker */}
                  <div 
                    className="absolute top-0 bottom-0 w-0.5 bg-yellow-500 z-10"
                    style={{ left: `${(minPassingPoints / maxPoints) * 100}%` }}
                  />
                  {/* Average score indicator */}
                  <Progress 
                    value={((data.average_score || 0) / maxPoints) * 100} 
                    className="h-full"
                  />
                </div>
                <p className="text-xs text-center text-muted-foreground">
                  Порог зачёта: {minPassingPoints} баллов
                </p>
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
            {data.grade_distribution && Object.keys(data.grade_distribution).length > 0 && (
              <div className="mt-4 pt-4 border-t">
                <p className="text-xs text-muted-foreground mb-2">Распределение оценок</p>
                <div className="flex gap-2">
                  {Object.entries(data.grade_distribution).map(([grade, count]) => (
                    <div 
                      key={grade} 
                      className={cn(
                        "flex-1 text-center py-2 rounded-lg text-sm font-medium",
                        grade === 'отл' && "bg-green-500/10 text-green-600 dark:text-green-400",
                        grade === 'хор' && "bg-blue-500/10 text-blue-600 dark:text-blue-400",
                        grade === 'уд' && "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400",
                        grade === 'неуд' && "bg-red-500/10 text-red-600 dark:text-red-400",
                      )}
                    >
                      <div className="text-lg font-bold">{count}</div>
                      <div className="text-xs opacity-80">{grade}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
        </BlurFade>
      )}
    </div>
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
            Требуется внимание куратора
          </p>
          <p className="text-sm text-red-600/80 dark:text-red-400/80">
            {failingCount} из {totalCount} студентов не получают зачёт
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
          Все студенты успешно справляются с курсом
        </p>
      </div>
    </div>
  );
}

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  description: string;
  color: 'default' | 'success' | 'destructive' | 'primary';
  borderColor: string;
  highlight?: boolean;
  isDecimal?: boolean;
}

function StatCard({ icon, label, value, description, color, borderColor, highlight, isDecimal }: StatCardProps) {
  const colorClasses = {
    default: 'text-foreground bg-muted',
    success: 'text-green-500 bg-green-500/10',
    destructive: 'text-red-500 bg-red-500/10',
    primary: 'text-blue-500 bg-blue-500/10',
  };

  return (
    <Card className={cn(
      "relative overflow-hidden transition-all border-l-4",
      borderColor,
      highlight && "ring-2 ring-red-500/30 bg-red-500/5"
    )}>
      <CardContent className="p-4">
        <div className={cn("p-2 rounded-lg w-fit mb-2", colorClasses[color])}>
          {icon}
        </div>
        <p className="text-2xl font-bold">
          <NumberTicker 
            value={value} 
            decimalPlaces={isDecimal ? 1 : 0}
            delay={0.1}
          />
        </p>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-xs text-muted-foreground/70 mt-1">{description}</p>
      </CardContent>
      {highlight && (
        <BorderBeam 
          size={80} 
          duration={4} 
          colorFrom="#ef4444" 
          colorTo="#f97316"
          borderWidth={2}
        />
      )}
    </Card>
  );
}
