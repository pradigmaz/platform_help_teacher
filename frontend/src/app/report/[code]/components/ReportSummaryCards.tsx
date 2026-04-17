'use client';

import { AlertTriangle, CheckCircle2, HelpCircle, TrendingUp, Users } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { MetricCard } from '@/components/ui/metric-card';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import { formatScoreValue } from '@/lib/score-format';
import type { PublicReportData, PublicStudentData } from '@/lib/api';
import type { ReportSubgroupFilter } from './reportFilters';

interface ReportSummaryCardsProps {
  data: PublicReportData;
  students: PublicStudentData[];
  selectedSubgroup: ReportSubgroupFilter;
}

export function ReportSummaryCards({ data, students, selectedSubgroup }: ReportSummaryCardsProps) {
  if (students.length === 0) {
    return null;
  }

  const scoredStudents = students.filter((student) => typeof student.total_score === 'number');
  const attendanceStudents = students.filter((student) => typeof student.attendance_rate === 'number');
  const labStudents = students.filter(
    (student) => typeof student.labs_completed === 'number' && typeof student.labs_total === 'number' && student.labs_total > 0,
  );

  const averageScore = scoredStudents.length > 0
    ? scoredStudents.reduce((total, student) => total + (student.total_score ?? 0), 0) / scoredStudents.length
    : undefined;

  const averageAttendance = attendanceStudents.length > 0
    ? attendanceStudents.reduce((total, student) => total + (student.attendance_rate ?? 0), 0) / attendanceStudents.length
    : data.attendance_stats?.average_rate;

  const averageLabCompletion = labStudents.length > 0
    ? labStudents.reduce((total, student) => {
      const completed = student.labs_completed ?? 0;
      const labsTotal = student.labs_total ?? 0;
      return total + (labsTotal > 0 ? (completed / labsTotal) * 100 : 0);
    }, 0) / labStudents.length
    : undefined;

  const atRiskCount = students.filter((student) => student.needs_attention).length;
  const passingCount = students.filter((student) => student.is_passing).length;
  const gradeDistribution = getGradeDistribution(students, data.grade_distribution, selectedSubgroup);
  const maxPoints = data.max_points ?? 35;
  const minPassingPoints = data.min_passing_points ?? 20;
  const subgroupLabel = selectedSubgroup === 'all' ? 'Вся группа' : `${selectedSubgroup} подгруппа`;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline" className="rounded-full px-3 py-1 text-sm font-medium">
          {subgroupLabel}
        </Badge>
        <p className="text-sm text-muted-foreground">
          Сводка пересчитана только по видимым студентам.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard tint="blue" interactive={false}>
          <SummaryStat
            icon={<Users className="h-4 w-4" />}
            label="Студентов в текущем срезе"
            value={String(students.length)}
            hint={`Всего в отчёте: ${data.total_students}`}
          />
        </MetricCard>

        {data.show_grades && (
          <MetricCard tint="cyan" interactive={false}>
            <SummaryStat
              icon={<TrendingUp className="h-4 w-4" />}
              label="Средний балл"
              value={averageScore !== undefined ? formatScoreValue(averageScore) : '—'}
              hint={data.max_points ? `Из ${formatScoreValue(data.max_points)} возможных` : undefined}
            >
              {averageScore !== undefined && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>0</span>
                    <span>{formatScoreValue(maxPoints)}</span>
                  </div>
                  <div className="relative">
                    <div
                      className="absolute top-0 z-10 h-2 w-px bg-amber-500"
                      style={{ left: `${(minPassingPoints / maxPoints) * 100}%` }}
                    />
                    <Progress value={(averageScore / maxPoints) * 100} className="h-2" />
                  </div>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <span>Порог зачёта: {formatScoreValue(minPassingPoints)}</span>
                    {data.grade_scale && (
                      <GradeScalePopover
                        gradeScale={data.grade_scale}
                        attestationType={data.attestation_type}
                        maxPoints={maxPoints}
                      />
                    )}
                  </div>
                </div>
              )}
            </SummaryStat>
          </MetricCard>
        )}

        {data.show_attendance && (
          <MetricCard tint="green" interactive={false}>
            <SummaryStat
              icon={<CheckCircle2 className="h-4 w-4" />}
              label="Средняя посещаемость"
              value={averageAttendance !== undefined ? `${Math.round(averageAttendance)}%` : '—'}
              hint="За выбранную аттестацию"
            />
          </MetricCard>
        )}

        <MetricCard tint={atRiskCount > 0 ? 'orange' : 'green'} interactive={false}>
          <SummaryStat
            icon={atRiskCount > 0 ? <AlertTriangle className="h-4 w-4" /> : <CheckCircle2 className="h-4 w-4" />}
            label={atRiskCount > 0 ? 'Нужно внимание' : 'Ситуация в группе'}
            value={atRiskCount > 0 ? String(atRiskCount) : String(passingCount || students.length)}
            hint={atRiskCount > 0 ? 'Студенты с риском по текущим данным' : 'Студенты идут без явного риска'}
          >
            {averageLabCompletion !== undefined && data.show_grades && (
              <p className="text-xs text-muted-foreground">
                Средняя готовность лабораторных: {Math.round(averageLabCompletion)}%
              </p>
            )}
          </SummaryStat>
        </MetricCard>
      </div>

      {(selectedSubgroup === 'all' || Object.values(gradeDistribution).some((count) => count > 0)) && data.show_grades && !data.is_early_semester && (
        <Card className="border-border/60 shadow-sm">
          <CardContent className="space-y-4 p-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-base font-semibold">Распределение оценок</h2>
                <p className="text-sm text-muted-foreground">
                  Показывает, как распределяются итоговые результаты по текущему срезу.
                </p>
              </div>
              {atRiskCount > 0 ? (
                <Badge variant="secondary" className="border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300">
                  {atRiskCount} требуют внимания
                </Badge>
              ) : (
                <Badge variant="secondary" className="border-green-500/30 bg-green-500/10 text-green-700 dark:text-green-300">
                  Критичных сигналов нет
                </Badge>
              )}
            </div>

            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {GRADE_CONFIG.map(({ key, label, tone }) => (
                <div
                  key={key}
                  className={cn('rounded-2xl border px-4 py-3', tone)}
                >
                  <p className="text-sm font-medium opacity-80">Оценка {label}</p>
                  <p className="mt-2 text-3xl font-semibold">{gradeDistribution[key] ?? 0}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

const GRADE_CONFIG = [
  {
    key: 'неуд',
    label: '2',
    tone: 'border-red-500/20 bg-red-500/5 text-red-700 dark:text-red-300',
  },
  {
    key: 'уд',
    label: '3',
    tone: 'border-amber-500/20 bg-amber-500/5 text-amber-700 dark:text-amber-300',
  },
  {
    key: 'хор',
    label: '4',
    tone: 'border-blue-500/20 bg-blue-500/5 text-blue-700 dark:text-blue-300',
  },
  {
    key: 'отл',
    label: '5',
    tone: 'border-green-500/20 bg-green-500/5 text-green-700 dark:text-green-300',
  },
] as const;

function getGradeDistribution(
  students: PublicStudentData[],
  fullDistribution: Record<string, number> | undefined,
  selectedSubgroup: ReportSubgroupFilter,
) {
  if (selectedSubgroup === 'all' && fullDistribution) {
    return fullDistribution;
  }

  return students.reduce<Record<string, number>>((result, student) => {
    if (student.grade) {
      result[student.grade] = (result[student.grade] ?? 0) + 1;
    }
    return result;
  }, {});
}

function SummaryStat({
  icon,
  label,
  value,
  hint,
  children,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  hint?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="space-y-3 p-5">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        {icon}
        <span>{label}</span>
      </div>
      <p className="text-3xl font-semibold tracking-tight">{value}</p>
      {hint && <p className="text-sm text-muted-foreground">{hint}</p>}
      {children}
    </div>
  );
}

interface GradeScalePopoverProps {
  gradeScale: Record<string, number[]>;
  attestationType?: string;
  maxPoints: number;
}

function GradeScalePopover({ gradeScale, attestationType = 'first', maxPoints }: GradeScalePopoverProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button className="inline-flex items-center transition-colors hover:text-foreground">
          <HelpCircle className="h-3.5 w-3.5" />
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-64" align="center">
        <div className="space-y-3">
          <div>
            <p className="text-sm font-medium">
              Шкала оценок {attestationType === 'first' ? 'для 1 аттестации' : 'для 2 аттестации'}
            </p>
            <p className="text-xs text-muted-foreground">Максимум: {formatScoreValue(maxPoints)} баллов</p>
          </div>
          <div className="space-y-2">
            {GRADE_CONFIG.map(({ key, label }) => {
              const range = gradeScale[key];
              if (!range) {
                return null;
              }

              return (
                <div key={key} className="flex items-center justify-between text-sm">
                  <span>Оценка {label}</span>
                  <span className="text-muted-foreground">
                    {formatScoreValue(range[0])}–{formatScoreValue(range[1])}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
